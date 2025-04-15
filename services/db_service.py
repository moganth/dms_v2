import sqlite3

from logger import get_logger

logger = get_logger(__name__)

db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL
    )
    """)
    db.commit()
    logger.info("DataBase Created Successfully")