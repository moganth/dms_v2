import docker
from fastapi import HTTPException, APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from schemas.docker_schema import *

from services import docker_service as ds
from services.db_service import get_user_by_username, insert_user
from services.auth_service import authenticate_user
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from services.auth_service import get_current_user, create_access_token, get_password_hash

from slowapi import Limiter
from slowapi.util import get_remote_address

from logger import get_logger
logger = get_logger(__name__)


client = docker.from_env()
auth_router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

@auth_router.post("/register", status_code=201)
def register(user: User):
    if get_user_by_username(user.username):
        logger.error("Username already registered")
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    user_id = insert_user(user.username, hashed_password, user.role)
    logger.info(f"User registered successfully with ID: {user_id}")
    return {"message": "User registered successfully", "user_id": user_id}

@auth_router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning("Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": user["username"], "role": user.get("role", "user")},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    logger.info(f"Token created for user {user['username']} with role {user.get('role', 'user')}")
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/login")
@limiter.limit("5/minute")
def login_to_docker(payload: DockerLoginSchema,
                    request: Request,
                    current_user: dict = Depends(get_current_user)):
    logger.info(f"Login successful by {current_user['username']} ")
    return ds.docker_login(payload.username, payload.password)