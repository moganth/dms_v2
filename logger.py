import logging
import os
from logging.handlers import RotatingFileHandler

from config import LOG_DIR, LOG_FILE

LOG_DIR = LOG_DIR
LOG_FILE = LOG_FILE
os.makedirs(LOG_DIR, exist_ok=True)  # Create 'logs/' directory if not present

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler with Rotation (5MB per file, keep 3 backups)
        file_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, LOG_FILE),
            maxBytes=5*1024*1024,
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
