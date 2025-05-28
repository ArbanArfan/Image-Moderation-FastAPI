# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Database settings
    MONGODB_URL: str = "mongodb+srv://arbanarfan1:isln0boMWmJlxG60@image-moderationv2.wvgqfk6.mongodb.net/?retryWrites=true&w=majority&appName=Image-ModerationV2"
    DATABASE_NAME: str = "image_moderation"
    
    # API settings
    PORT: int = 7000
    HOST: str = "0.0.0.0"
    DEBUG: bool = False
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
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