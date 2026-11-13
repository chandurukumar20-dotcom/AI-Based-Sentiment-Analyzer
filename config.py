import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "sentiment-secret-key-super-secure-2026")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    PORT = int(os.getenv("PORT", 5000))

    # MongoDB Settings
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/sentiment_db")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "sentiment_db")
    MONGO_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", 3000))

    # Uploads directory
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB max
    ALLOWED_EXTENSIONS = {"csv"}

    # NLP Model configuration
    MODEL_NAME = os.getenv("MODEL_NAME", "cardiffnlp/twitter-roberta-base-sentiment-latest")
    USE_TRANSFORMERS = os.getenv("USE_TRANSFORMERS", "False").lower() in ("true", "1", "t")
    FALLBACK_TO_VADER = os.getenv("FALLBACK_TO_VADER", "True").lower() in ("true", "1", "t")

    # Local fallback storage path if MongoDB is not accessible
    LOCAL_DATA_DIR = BASE_DIR / "data"
    LOCAL_DB_FILE = LOCAL_DATA_DIR / "sentiment_records.json"


# Ensure directories exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.LOCAL_DATA_DIR, exist_ok=True)
