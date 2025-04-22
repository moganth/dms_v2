import docker
from fastapi import APIRouter, Depends, Query

from schemas.docker_schema import *

from services import docker_service as ds
from services.auth_service import get_current_user

from logger import get_logger
logger = get_logger(__name__)

client = docker.from_env()
volume_router = APIRouter()


@volume_router.post("/volume/create")
def create_docker_volume(payload: VolumeSchema,
                         current_user: dict = Depends(get_current_user)):
    result = ds.create_volume(payload.volume_name)
    logger.info(f"Volume '{payload.volume_name}' deleted successfully by {current_user['username']}")
    return {
            "message": f"Volume '{payload.volume_name}' deleted successfully by {current_user['username']}",
            "result": result
        }

@volume_router.get("/volumes")
def list_docker_volumes(current_user: dict = Depends(get_current_user)):
    logger.info(f"Volumes listed by {current_user['username']}")
    return ds.list_volumes()

@volume_router.delete("/volume/delete")
def delete_docker_volume(current_user: dict = Depends(get_current_user),
                         volume_name: str = Query(...)):
    result = ds.delete_volume(volume_name)
    logger.info(f"Volume '{volume_name}' deleted successfully by {current_user['username']}")
    return {
        "message": f"Volume '{volume_name}' deleted successfully by {current_user['username']}",
        "result": result
    }