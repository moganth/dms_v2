import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DOCKER_REGISTRY = "https://index.docker.io/v1/"

# Security config
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

LOG_FILE = "DMS_V2.log"
LOG_DIR = "logs"