import os
from pathlib import Path
from flask import Flask
from pydantic_settings import BaseSettings, SettingsConfigDict


# Get the base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Create the absolute path
path_obj = BASE_DIR / "db_test" / "school-system_1.db"



ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Upload Configuration
UPLOAD_FOLDER = BASE_DIR / "uploads"

class Config(BaseSettings):
    """Application configuration using Pydantic Settings."""
    JWT_REFRESH_TOKEN_EXPIRES:int
    JWT_ACCESS_TOKEN_EXPIRES:int
    
    
    # Secret Keys
    SECRET_KEY: str
    CLOUDINARY_SECRET_KEY: str
    JWT_SECRET_KEY: str
    super_admin_password:str
    TEST_DB: str = f"sqlite:///{path_obj.as_posix()}"
    
    # Payment Configuration
    PAYSTACK_LIVE_KEY: str
    PAYSTACK_TEST_KEY: str
    
    # Database Configuration
    TEST_DATABASE_URL: str
    PROD_DATABASE_URL: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool
    
    # Twilio Configuration
    Twilio_sid: str
    Twilio_token: str
    
    # Upload Configuration
    # UPLOAD_FOLDER: Path
    
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Create a global config instance
config = Config()

def app_config(app: Flask):
    
    app.config.from_mapping(config.model_dump())
class Settings:
    PROJECT_NAME: str = "Clearance System"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "Backend for Clearance System"
    API_PREFIX: str = "/api/v1"
