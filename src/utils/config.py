from .util import get_env_value
from datetime import timedelta
import os

class Config:
    DEBUG = get_env_value("DEBUG") == 'True'
    SECRET_KEY = get_env_value("SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=20)
    JWT_IDENTITY_CLAIM = "entity_id"
    
    # Set the upload folder
    UPLOAD_FOLDER = 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_file_path(filename):
    return os.path.join(Config.UPLOAD_FOLDER, filename)


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = get_env_value("URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = get_env_value("SQLALCHEMY_TRACK_MODIFICATIONS") == 'True'


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = get_env_value("URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = get_env_value("SQLALCHEMY_TRACK_MODIFICATIONS") == 'True'
