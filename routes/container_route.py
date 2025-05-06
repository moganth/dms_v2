import os
import docker
from fastapi import HTTPException, APIRouter, Depends, Request, Query
from fastapi.responses import PlainTextResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from schemas.docker_schema import *

from services import docker_service as ds
from config import LOG_FILE, LOG_DIR
from services.auth_service import role_required,get_current_user

from logger import get_logger
logger = get_logger(__name__)


docker_client = docker.from_env()
container_router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

@container_router.post("/container/run")
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

@container_router.post("/pod/run")
def run_pod(payload: RunPodRequest,
                  current_user: dict = Depends(get_current_user)):
    try:
        result = ds.run_pod(payload.image_name, payload.container_name, payload.container_port)
        logger.info(f"Pod '{result['pod_name']}' created by {current_user['username']}")
        return {
            "message": f"Pod '{result['pod_name']}' created successfully by {current_user['username']}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error creating pod: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@container_router.post("/container/stop")
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

@container_router.post("/container/start")
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

@container_router.post("/container/restart")
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

@container_router.post("/container/remove")
def remove_container(payload: ContainerRunRequest,
                     current_user: dict = Depends(role_required(["admin"]))):
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

@container_router.get("/logs/{container_name}")
@limiter.limit("5/minute")
def get_logs(container_name: str,
             request: Request,
             current_user: dict = Depends(role_required(["admin", "user"]))):
    logger.info(f"Container logs listed by {current_user['username']} on {container_name}")
    try:
        return ds.get_logs(container_name)
    except Exception as e:
        logger.error(f"Error getting logs for container {container_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@container_router.get("/logs/")
def get_logs_with_pods(
    pod_name: str = Query(..., description="Kubernetes Pod Name"),
    container_name: str = Query(None, description="Container name inside the pod"),
    request: Request = None,
    current_user: dict = Depends(role_required(["admin", "user"]))
):
    logger.info(f"Fetching logs for pod={pod_name}, container={container_name} by {current_user['username']}")
    try:
        return ds.get_logs_with_pods(pod_name, container_name)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@container_router.get("/ps")
def docker_ps(current_user: dict = Depends(get_current_user)):
    logger.info(f"Docker ps performed {current_user['username']}")
    return ds.docker_ps()

@container_router.get("/logs", response_class=PlainTextResponse)
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

@container_router.get("/protected")
def protected_route(current_user: dict = Depends(get_current_user)):
    logger.info({"message": f"Hello, {current_user['username']}! You are authenticated."})
    return {"message": f"Hello, {current_user['username']}! You are authenticated."}

#---------------------------------------------------------------------------------------------------------------