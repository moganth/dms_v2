import os
import subprocess
from uuid import uuid4

import docker
from kubernetes import client, config
from docker.errors import APIError
from config import DOCKER_REGISTRY

# Load cluster config
# config.load_incluster_config()
# v1 = client.CoreV1Api()
v1 = None

try:
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        config.load_incluster_config()
    else:
        config.load_kube_config()
    v1 = client.CoreV1Api()
except Exception as e:
    print(f"Kubernetes disabled: {e}")

docker_client = docker.from_env()

def docker_login(username: str, password: str):
    try:
        login_response = docker_client.login(username=username, password=password, registry=DOCKER_REGISTRY)
        return {"status": "success", "message": "Logged in to Docker Hub"}
    except APIError as e:
        return {"error": str(e)}

def build_image(dockerfile_path: str, image_name: str, dockerfile_name: str = "Dockerfile"):
    try:
        image, logs = docker_client.images.build(
            path=dockerfile_path,
            tag=image_name,
            dockerfile=dockerfile_name,
            rm=True
        )
        log_output = ""
        for chunk in logs:
            if 'stream' in chunk:
                log_output += chunk['stream']
        return f"Image '{image_name}' built successfully.\nLogs:\n{log_output}"
    except Exception as e:
        raise Exception(f"Build failed: {e}")
#--------------------------------------------------------------------------------------------------------------------
def run_command(command: list):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return {"output": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr.strip()}

# Clone the GitHub repository to the home directory
def clone_github_repo(github_url: str, repo_name: str, destination_dir: str = "/home/ubuntu"):
    try:
        # Ensure the destination directory exists
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        # Use the provided repo_name
        destination_path = os.path.join(destination_dir, repo_name)

        # Clone the GitHub repository to the specified path
        if os.path.exists(destination_path):  # Check if directory already exists
            return {"error": f"Directory {destination_path} already exists."}

        clone_command = ["git", "clone", github_url, destination_path]
        result = subprocess.run(clone_command, capture_output=True, text=True, check=True)
        return {"message": f"Repository cloned to {destination_path}", "output": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to clone repository: {e.stderr.strip()}"}

# Build a Docker image from the cloned repository
def build_image_from_repo(github_url: str, image_name: str, repo_name: str):
    try:
        # Clone the repository first
        clone_response = clone_github_repo(github_url, repo_name)
        if "error" in clone_response:
            return clone_response  # Return error if cloning fails

        # Assuming the repository contains a Dockerfile at the root level
        destination_dir = os.path.join("/home/ubuntu", repo_name)  # Path where the repo is cloned

        # Build the Docker image
        build_command = ["docker", "build", "-t", image_name, destination_dir]
 
        # Run the build command
        build_response = run_command(build_command)
        return build_response
    except Exception as e:
        return {"error": str(e)}

# Push a Docker image to GHCR
def push_image_to_ghcr(github_url: str, repo_name: str, image_name: str, token: str):
    try:
        # Log in to GitHub Container Registry
        login_command = [
            "docker", "login", "ghcr.io", "-u", "moganth", "--password-stdin"
        ]
        # Pass the token securely
        subprocess.run(login_command, input=token, text=True, check=True)

        # Push the image to GHCR
        push_command = ["docker", "push", image_name]
        push_response = run_command(push_command)
        return push_response
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to push image: {e.stderr.strip()}"}


# Pull a Docker image from GHCR
def pull_image_from_ghcr(github_url: str, repo_name: str, image_name: str):
    try:
        pull_command = ["docker", "pull", image_name]
        pull_response = run_command(pull_command)
        return pull_response
    except Exception as e:
        return {"error": str(e)}
#--------------------------------------------------------------------------------------------------------------------

def push_image(local_image_name: str, repository_name: str, username: str, password: str):
    try:
        # Login to Docker Hub
        docker_client.login(username=username, password=password)

        # Tag the local image with the Docker Hub repository name
        image = docker_client.images.get(local_image_name)
        image.tag(repository_name)

        # Push the image to Docker Hub
        response = docker_client.images.push(repository_name)
        return f"Image '{local_image_name}' pushed as '{repository_name}' to Docker Hub.\nResponse:\n{response}"
    except Exception as e:
        raise Exception(f"Push failed: {e}")

def pull_image(image_name: str, repository_name: str):
    try:
        full_image_name = f"{repository_name}:{image_name.split(':')[-1]}"
        image = docker_client.images.pull(full_image_name)
        return {"status": "success", "message": f"Image '{full_image_name}' pulled successfully"}
    except APIError as e:
        return {"error": str(e)}

def list_images():
    images = docker_client.images.list()
    image_list = []
    for img in images:
        image_list.append({
            "id": img.id,
            "tags": img.tags,
            "short_id": img.short_id
        })
    return image_list

def delete_image(image_name: str):
    try:
        docker_client.images.get(image_name)
        docker_client.images.remove(image_name, force=True)
        return {"status": "success", "message": f"Image {image_name} removed"}
    except docker.errors.ImageNotFound:
        return {"error": f"Image {image_name} not found"}
    except APIError as e:
        return {"error": str(e)}

def get_logs(container_name: str):
    try:
        container = docker_client.containers.get(container_name)
        logs = container.logs(timestamps=True).decode('utf-8')
        log_lines = logs.strip().split('\n')
        return {"container": container_name, "logs": log_lines}
    except Exception as e:
        raise Exception(f"Failed to get logs for container '{container_name}': {e}")

def get_logs_with_pods(pod_name: str, container_name: str = None, namespace: str = "default"):
    try:
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container_name,
            timestamps=True,
        )
        return {"pod": pod_name, "logs": logs.strip().split("\n")}
    except client.exceptions.ApiException as e:
        raise Exception(f"Kubernetes API error: {e.reason}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")

def docker_ps():
    try:
        containers = docker_client.containers.list()
        result = []
        for container in containers:
            result.append({
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags
            })
        return result
    except Exception as e:
        raise Exception(f"Failed to list containers: {e}")

def run_container(image_name: str, container_name: str, ports: dict = None, environment: dict = None, volumes: dict = None):
    try:
        container = docker_client.containers.run(
            image_name,
            name=container_name,
            ports=ports,
            environment=environment,
            volumes=volumes,  # Format: {"/host/path": {"bind": "/container/path", "mode": "rw"}}
            detach=True
        )
        return {"status": "success", "message": f"Container '{container_name}' started successfully", "container_id": container.id}
    except Exception as e:
        return {"error": str(e)}


def run_pod(image_name: str, container_name: str, container_port: int, namespace: str = "default"):
    try:
        pod_name = f"{container_name}-{str(uuid4())[:8]}"

        docker_sock_volume = client.V1Volume(
            name="docker-sock",
            host_path=client.V1HostPathVolumeSource(
                path="/var/run/docker.sock",
                type="Socket"
            )
        )

        docker_sock_volume_mount = client.V1VolumeMount(
            name = "docker-sock",
            mount_path = "/var/run/docker.sock"
        )

        container = client.V1Container(
            name = container_name,
            image = image_name,
            ports = [client.V1ContainerPort(container_port=container_port)],
            volume_mounts=[docker_sock_volume_mount]
        )

        pod_spec = client.V1PodSpec(
            containers=[container],
            volumes=[docker_sock_volume],
            restart_policy="Never"
        )

        pod_manifest = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name, labels={"app": container_name}),
            spec=pod_spec
        )

        # pod_manifest = client.V1Pod(
        #     metadata=client.V1ObjectMeta(name=pod_name, labels={"app": container_name}),
        #     spec=client.V1PodSpec(
        #         containers=[
        #             client.V1Container(
        #                 name=container_name,
        #                 image=image_name,
        #                 ports=[client.V1ContainerPort(container_port=container_port)]
        #             )
        #         ],
        #         restart_policy="Never"
        #     )
        # )

        v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
        return {
            "status": "success",
            "message": f"Pod '{pod_name}' created successfully using image '{image_name}'",
            "pod_name": pod_name
        }
    except client.exceptions.ApiException as e:
        raise Exception(f"Kubernetes API error: {e.reason}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


def stop_container(container_name: str):
    try:
        container = docker_client.containers.get(container_name)
        container.stop()
        return {"status": "success", "message": f"Container '{container_name}' stopped"}
    except Exception as e:
        return {"error": str(e)}

def start_container(container_name: str):
    try:
        container = docker_client.containers.get(container_name)
        container.start()
        return {"status": "success", "message": f"Container '{container_name}' started"}
    except Exception as e:
        return {"error": str(e)}

def restart_container(container_name: str):
    try:
        container = docker_client.containers.get(container_name)
        container.restart()
        return {"status": "success", "message": f"Container '{container_name}' restarted"}
    except Exception as e:
        return {"error": str(e)}

def remove_container(container_name: str):
    try:
        container = docker_client.containers.get(container_name)
        container.remove()
        return {"status": "success", "message": f"Container '{container_name}' removed"}
    except Exception as e:
        return {"error": str(e)}

def create_volume(volume_name: str):
    try:
        volume = docker_client.volumes.create(name=volume_name)
        return {"status": "success", "message": f"Volume '{volume_name}' created", "volume_id": volume.id}
    except Exception as e:
        return {"error": str(e)}

def list_volumes():
    try:
        volumes = docker_client.volumes.list()
        return [{"name": v.name, "driver": v.attrs.get("Driver")} for v in volumes]
    except Exception as e:
        return {"error": str(e)}

def delete_volume(volume_name: str):
    try:
        volume = docker_client.volumes.get(volume_name)
        volume.remove()
        return {"status": "success", "message": f"Volume '{volume_name}' deleted"}
    except Exception as e:
        return {"error": str(e)}