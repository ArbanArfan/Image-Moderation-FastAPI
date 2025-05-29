# config.py
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os
load_dotenv()

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Database settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "image_moderation")
    
    # API settings
    PORT: int = os.getenv("PORT", 7000)
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    
    # Image processing settings
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    # Moderation settings
    SAFETY_THRESHOLD: float = 0.7
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()