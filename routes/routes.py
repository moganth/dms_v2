import docker
from fastapi import HTTPException, APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from schemas.docker_schema import (DockerImageSchema, DockerLoginSchema, BuildImagePayload, PushImagePayload,
                                   PullImagePayload, ContainerRunRequest, VolumeSchema, BuildRequest, User, Token,)
from services import docker_service as ds
from services.docker_service import build_image_from_repo
from services.db_service import db
from services.db_service import cursor
from services.auth_service import get_user, authenticate_user
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from services.auth_service import get_current_user, create_access_token, get_password_hash

client = docker.from_env()
router = APIRouter()

@router.post("/login")
def login_to_docker(payload: DockerLoginSchema,
                    current_user: dict = Depends(get_current_user)):
    return ds.docker_login(payload.username, payload.password)

@router.post("/docker/build from github repo")
def build_image(request: BuildRequest,
                current_user: dict = Depends(get_current_user)):
    github_url = request.github_url
    image_name = request.image_name
    repo_name = request.repo_name
    result = build_image_from_repo(github_url, image_name, repo_name)
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
        return {
            "message": f"image '{payload.image_name}' build by {current_user['username']}",
            "result": result
        }
    except Exception as e:
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
        return {
            "message": f"image '{payload.local_image_name}' pushed by {current_user['username']} to {payload.repository_name}",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pull")
def pull_image(payload: PullImagePayload,
               current_user: dict = Depends(get_current_user)):
    try:
        result = ds.pull_image(payload.image_name, payload.repository_name)
        return {
            "message": f"image '{payload.image_name}' initiated successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/images")
def list_all_images(current_user: dict = Depends(get_current_user)):
    return ds.list_images()

@router.delete("/images")
def remove_image(image_name: str = Query(...),
                 current_user: dict = Depends(get_current_user)):
    result = ds.delete_image(image_name)
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
        return {
            "message": f"container '{payload.container_name}' initiated successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/container/stop")
def stop_container(payload: ContainerRunRequest,
                   current_user: dict = Depends(get_current_user)):
    try:
        result = ds.stop_container(payload.container_name)
        return {
            "message": f"container '{payload.container_name}' deleted successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/container/start")
def start_container(payload: ContainerRunRequest,
                    current_user: dict = Depends(get_current_user)):
    try:
        result = ds.start_container(payload.container_name)
        return {
            "message": f"container '{payload.container_name}' deleted successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/container/restart")
def restart_container(payload: ContainerRunRequest,
                      current_user: dict = Depends(get_current_user)):
    try:
        result = ds.restart_container(payload.container_name)
        return {
            "message": f"container '{payload.container_name}' deleted successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/container/remove")
def remove_container(payload: ContainerRunRequest,
                     current_user: dict = Depends(get_current_user)):
    try:
        result = ds.remove_container(payload.container_name)
        return {
            "message": f"container '{payload.container_name}' deleted successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{container_name}")
def get_logs(container_name: str,
             current_user: dict = Depends(get_current_user)):
    return ds.get_logs(container_name)

@router.get("/ps")
def docker_ps(current_user: dict = Depends(get_current_user)):
    return ds.docker_ps()

@router.post("/volume/create")
def create_docker_volume(payload: VolumeSchema,
                         current_user: dict = Depends(get_current_user)):
    result = ds.create_volume(payload.volume_name)
    return {
            "message": f"Volume '{payload.volume_name}' deleted successfully by {current_user['username']}",
            "result": result
        }

@router.get("/volumes")
def list_docker_volumes(current_user: dict = Depends(get_current_user)):
    return ds.list_volumes()

@router.delete("/volume/delete")
def delete_docker_volume(current_user: dict = Depends(get_current_user),
                         volume_name: str = Query(...)):
    result = ds.delete_volume(volume_name)
    return {
        "message": f"Volume '{volume_name}' deleted successfully by {current_user['username']}",
        "result": result
    }

 #-----------------------------------------------------------------------------------------------

@router.post("/register", status_code=201)
def register(user: User):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    cursor.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)",
                   (user.username, hashed_password))
    db.commit()
    return {"message": "User registered successfully"}

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user["username"]},
                                       expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/protected")
def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello, {current_user['username']}! You are authenticated."}

#---------------------------------------------------------------------------------------------------------------