from pydantic import BaseModel
from typing import Optional, Dict

class ImageSchema(BaseModel):
    image_name: str

class BuildRequest(BaseModel):
    github_url: str
    image_name: str
    repo_name: str

class GHCRImageRequest(BaseModel):
    github_url: str
    repo_name: str
    image_name: str
    token: str

class ContainerSchema(BaseModel):
    image_name: str
    container_name: str

class DockerLoginSchema(BaseModel):
    username: str = "moganthkumar"
    password: str = "7010690656@Mk"

class DockerImageSchema(BaseModel):
    image_name: str
    repository_name: str = "moganthkumar/moganth" # Docker Hub repository name (e.g., username/repository)

class BuildImagePayload(BaseModel):
    image_name: str
    dockerfile_path: str = "/app"
    dockerfile_name: str = "Dockerfile"

class PushImagePayload(BaseModel):
    local_image_name: str
    repository_name: str = "moganthkumar/moganth"
    username: str = "moganthkumar"
    password: str = "7010690656@Mk"

class PullImagePayload(BaseModel):
    image_name: str
    repository_name: str

class ContainerRunRequest(BaseModel):
    image_name: str
    container_name: str
    ports: Optional[Dict[str, str]] = None
    environment: Optional[Dict[str, str]] = None
    volume_name: Optional[str] = None
    mount_path: Optional[str] = None
    # environment: Optional[Dict[str, str]] = None # Example: {"80": "8080"}
    # volumes: Optional[Dict[str, Dict[str, str]]] = None  # Example: {"/host": {"bind": "/container", "mode": "rw"}}

class VolumeSchema(BaseModel):
    volume_name: str

class User(BaseModel):
    username: str
    password: str
    role: str = "user"

class Token(BaseModel):
    access_token: str
    token_type: str

class RunPodRequest(BaseModel):
    image_name: str
    container_name: str
    container_port: int