import docker
from fastapi import HTTPException, APIRouter, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from schemas.docker_schema import *

from services import docker_service as ds
from services.docker_service import build_image_from_repo, push_image_to_ghcr, pull_image_from_ghcr
from services.auth_service import get_current_user

from logger import get_logger
logger = get_logger(__name__)

client = docker.from_env()
image_router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

@image_router.post("/docker/build from github repo")
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


@image_router.post("/docker/push to ghcr")
def push_image(request: GHCRImageRequest, current_user: dict = Depends(get_current_user)):
    github_url = request.github_url
    repo_name = request.repo_name
    image_name = request.image_name
    token = request.token  # Assuming the token is sent in the request

    # Pass the token to the service function
    result = push_image_to_ghcr(github_url, repo_name, image_name, token)

    logger.info(f"image '{request.image_name}' pushed to GHCR by {current_user['username']}")
    return {
        "message": f"image '{request.image_name}' pushed to GHCR by {current_user['username']}",
        "result": result
    }

@image_router.post("/docker/pull from ghcr")
def pull_image(request: GHCRImageRequest,
               current_user: dict = Depends(get_current_user)):
    github_url = request.github_url
    repo_name = request.repo_name
    image_name = request.image_name
    result = pull_image_from_ghcr(github_url, repo_name, image_name)
    logger.info(f"image '{request.image_name}' pulled from GHCR by {current_user['username']}")
    return {
        "message": f"image '{request.image_name}' pulled from GHCR by {current_user['username']}",
        "result": result
    }

@image_router.post("/docker/build")
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

@image_router.post("/docker/push")
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

@image_router.post("/pull")
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

@image_router.get("/images")
@limiter.limit("5/minute")
def list_all_images(request: Request,
                    current_user: dict = Depends(get_current_user)):
    logger.info(f"Images listed by {current_user['username']}")
    return ds.list_images()

@image_router.delete("/images")
def remove_image(image_name: str = Query(...),
                 current_user: dict = Depends(get_current_user)):
    result = ds.delete_image(image_name)
    logger.info(f"image '{image_name}' initiated successfully by {current_user['username']}")
    return {
                "message": f"image '{image_name}' initiated successfully by {current_user['username']}",
                "result": result
            }