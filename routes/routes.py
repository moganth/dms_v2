import os
import docker
from fastapi import HTTPException, APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# from schemas.docker_schema import (DockerImageSchema, DockerLoginSchema, BuildImagePayload, PushImagePayload,
#                                    PullImagePayload, ContainerRunRequest, VolumeSchema, BuildRequest, User, Token)
from schemas.docker_schema import *

from services import docker_service as ds
from services.docker_service import build_image_from_repo
from services.db_service import db
from services.db_service import cursor
from services.auth_service import get_user, authenticate_user
from config import ACCESS_TOKEN_EXPIRE_MINUTES, LOG_FILE, LOG_DIR
from services.auth_service import get_current_user, create_access_token, get_password_hash

from slowapi import Limiter
from slowapi.util import get_remote_address

from logger import get_logger
logger = get_logger(__name__)


client = docker.from_env()
router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
def login_to_docker(payload: DockerLoginSchema,
                    request: Request,
                    current_user: dict = Depends(get_current_user)):
    logger.info(f"Login successful by {current_user['username']} ")
    return ds.docker_login(payload.username, payload.password)

@router.post("/docker/build from github repo")
def build_image(request: BuildRequest,
                current_user: dict = Depends(get_current_user)):
    github_url = request.github_url
    image_name = request.image_name
    repo_name = request.repo_name
    result = build_image_from_repo(github_url, image_name, repo_name)
    logger.info(f"image '{request.image_name}' build by {current_user['username']} from {request.github_url}")
    return {
        "message": f"image '{request.image_name}' build by {current_user['username']} from {request.github_url}",
        "result": result
    }

@router.post("/docker/build")
def build_image(payload: BuildImagePayload,
                current_user: dict = Depends(get_current_user)):
    try:
        build_response = ds.build_image(
            dockerfile_path=payload.dockerfile_path,
            image_name=payload.image_name,
            dockerfile_name=payload.dockerfile_name
        )
        result = {"message": build_response}
        logger.info(f"image '{payload.image_name}' build by {current_user['username']}")
        return {
            "message": f"image '{payload.image_name}' build by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error building the image {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/docker/push")
def push_image(payload: PushImagePayload,
               current_user: dict = Depends(get_current_user)):
    try:
        push_response = ds.push_image(
            local_image_name=payload.local_image_name,
            repository_name=payload.repository_name,
            username=payload.username,
            password=payload.password
        )
        result = {"message": push_response}
        logger.info(f"image '{payload.local_image_name}' pushed by {current_user['username']} to {payload.repository_name}")
        return {
            "message": f"image '{payload.local_image_name}' pushed by {current_user['username']} to {payload.repository_name}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error pushing the image {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pull")
def pull_image(payload: PullImagePayload,
               current_user: dict = Depends(get_current_user)):
    try:
        result = ds.pull_image(payload.image_name, payload.repository_name)
        logger.info(f"image '{payload.image_name}' initiated successfully by {current_user['username']}")
        return {
            "message": f"image '{payload.image_name}' initiated successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error Pulling the image {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/images")
def list_all_images(current_user: dict = Depends(get_current_user)):
    logger.info(f"Images listed by {current_user['username']}")
    return ds.list_images()

@router.delete("/images")
def remove_image(image_name: str = Query(...),
                 current_user: dict = Depends(get_current_user)):
    result = ds.delete_image(image_name)
    logger.info(f"image '{image_name}' initiated successfully by {current_user['username']}")
    return {
                "message": f"image '{image_name}' initiated successfully by {current_user['username']}",
                "result": result
            }

# Container Endpoints
@router.post("/container/run")
def run_container(payload: ContainerRunRequest,
                  current_user: dict = Depends(get_current_user)):
    try:
        result = ds.run_container(payload.image_name, payload.container_name, payload.ports, payload.environment)
        logger.info(f"container '{payload.container_name}' initiated successfully by {current_user['username']}")
        return {
            "message": f"container '{payload.container_name}' initiated successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error running the container {payload.container_name}, {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/container/stop")
def stop_container(payload: ContainerRunRequest,
                   current_user: dict = Depends(get_current_user)):
    try:
        result = ds.stop_container(payload.container_name)
        logger.info(f"container '{payload.container_name}' deleted successfully by {current_user['username']}")
        return {
            "message": f"container '{payload.container_name}' deleted successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error stopping the container {payload.container_name}, {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/container/start")
def start_container(payload: ContainerRunRequest,
                    current_user: dict = Depends(get_current_user)):
    try:
        result = ds.start_container(payload.container_name)
        logger.info(f"container '{payload.container_name}' deleted successfully by {current_user['username']}")
        return {
            "message": f"container '{payload.container_name}' deleted successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error starting the container {payload.container_name}, {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/container/restart")
def restart_container(payload: ContainerRunRequest,
                      current_user: dict = Depends(get_current_user)):
    try:
        result = ds.restart_container(payload.container_name)
        logger.info(f"container '{payload.container_name}' deleted successfully by {current_user['username']}")
        return {
            "message": f"container '{payload.container_name}' deleted successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error restarting container: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/container/remove")
def remove_container(payload: ContainerRunRequest,
                     current_user: dict = Depends(get_current_user)):
    try:
        result = ds.remove_container(payload.container_name)
        logger.info(f"container '{payload.container_name}' deleted successfully by {current_user['username']}")
        return {
            "message": f"container '{payload.container_name}' deleted successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error removing volume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{container_name}")
def get_logs(container_name: str,
             current_user: dict = Depends(get_current_user)):
    logger.info(f"Container logs listed by {current_user['username']} on {container_name}")
    try:
        return ds.get_logs(container_name)
    except Exception as e:
        logger.error(f"Error getting logs for container {container_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ps")
def docker_ps(current_user: dict = Depends(get_current_user)):
    logger.info(f"Docker ps performed {current_user['username']}")
    return ds.docker_ps()

@router.post("/volume/create")
def create_docker_volume(payload: VolumeSchema,
                         current_user: dict = Depends(get_current_user)):
    result = ds.create_volume(payload.volume_name)
    logger.info(f"Volume '{payload.volume_name}' deleted successfully by {current_user['username']}")
    return {
            "message": f"Volume '{payload.volume_name}' deleted successfully by {current_user['username']}",
            "result": result
        }

@router.get("/volumes")
def list_docker_volumes(current_user: dict = Depends(get_current_user)):
    logger.info(f"Volumes listed by {current_user['username']}")
    return ds.list_volumes()

@router.delete("/volume/delete")
def delete_docker_volume(current_user: dict = Depends(get_current_user),
                         volume_name: str = Query(...)):
    result = ds.delete_volume(volume_name)
    logger.info(f"Volume '{volume_name}' deleted successfully by {current_user['username']}")
    return {
        "message": f"Volume '{volume_name}' deleted successfully by {current_user['username']}",
        "result": result
    }

@router.get("/logs", response_class=PlainTextResponse)
def read_logs(current_user: dict = Depends(get_current_user)):
    log_path = os.path.join(LOG_DIR, LOG_FILE)
    if not os.path.exists(log_path):
        logger.error("Log file not found")
        raise HTTPException(status_code=404, detail="Log file not found")

    try:
        with open(log_path, "r") as log_file:
            log_content = log_file.read()
            return log_content
    except Exception as e:
        logger.error(f"Failed to read log file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {str(e)}")

 #-----------------------------------------------------------------------------------------------

@router.post("/register", status_code=201)
def register(user: User):
    if get_user(user.username):
        logger.error("Username already registered")
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    cursor.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)",
                   (user.username, hashed_password))
    db.commit()
    logger.info({"User registered successfully"})
    return {"message": "User registered successfully"}

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning("Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user["username"]},
                                       expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    logger.info({"access_token": access_token, "token_type": "bearer"})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/protected")
def protected_route(current_user: dict = Depends(get_current_user)):
    logger.info({"message": f"Hello, {current_user['username']}! You are authenticated."})
    return {"message": f"Hello, {current_user['username']}! You are authenticated."}

#---------------------------------------------------------------------------------------------------------------