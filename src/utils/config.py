import os
from pathlib import Path
from flask import Flask
from pydantic_settings import BaseSettings, SettingsConfigDict


# Get the base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Upload Configuration
UPLOAD_FOLDER = BASE_DIR / "qplus" / "src" / "uploads"

class Config(BaseSettings):
    """Application configuration using Pydantic Settings."""
    
    # Secret Keys
    SECRET_KEY: str
    CLOUDINARY_SECRET_KEY: str
    JWT_SECRET_KEY: str
    
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
