from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

from services.db_service import get_user_by_username
from config import SECRET_KEY, ALGORITHM
from logger import get_logger

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def get_user(username: str):
    user = get_user_by_username(username)
    if user:
        # Convert MongoDB _id to string if needed for JWT
        user_dict = {
            "id": str(user["_id"]),
            "username": user["username"],
            "hashed_password": user["hashed_password"]
        }
        logger.info(f"User found: {username}")
        return user_dict
    logger.info(f"User not found: {username}")
    return None

def verify_password(plain_password, hashed_password):
    result = pwd_context.verify(plain_password, hashed_password)
    if result:
        logger.info("Password verified successfully")
    else:
        logger.info("Password verification failed")
    return result

def get_password_hash(password):
    logger.info("Password hashed successfully")
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info("Token created Successfully")
    return encoded_jwt

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        logger.error("Password or user is Invalid")
        return False
    logger.info(f"User {username} Authenticated")
    return user

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error(f"Username not found")
            raise credentials_exception
    except JWTError:
        logger.error(f"{credentials_exception}")
        raise credentials_exception
    user = get_user(username)
    if user is None:
        logger.error(f"{credentials_exception}")
        raise credentials_exception
    return user