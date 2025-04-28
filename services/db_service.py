import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from logger import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "docker_management")

try:
    client = MongoClient(MONGODB_URI)
    client.admin.command('ping')
    logger.info("Connected to MongoDB successfully")
    db = client[DB_NAME]
    users_collection = db["users"]
    users_collection.create_index("username", unique=True)

except ConnectionFailure as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise


def init_db():
    if "users" not in db.list_collection_names():
        db.create_collection("users")
        logger.info("Users collection created successfully")
    logger.info("Database initialized successfully")


def get_user_by_username(username: str):
    user = users_collection.find_one({"username": username})
    logger.info(f"User lookup for username: {username}")
    return user


def insert_user(username: str, hashed_password: str, role: str = "user"):
    try:
        user_id = users_collection.insert_one({
            "username": username,
            "hashed_password": hashed_password,
            "role": role
        }).inserted_id
        logger.info(f"User {username} registered successfully with ID: {user_id}, role: {role}")
        return str(user_id)
    except Exception as e:
        logger.error(f"Error inserting user: {e}")
        raise