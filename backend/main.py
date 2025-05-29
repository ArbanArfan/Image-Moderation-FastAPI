# main.py
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime
from typing import List, Optional
import io
from PIL import Image
import hashlib
import secrets
import logging

from database import Database
from models import TokenCreate, TokenResponse, ModerationResult, UsageRecord
from image_moderator import ImageModerator
from config import settings
from rich.console import Console

console = Console()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
db = Database()
image_moderator = ImageModerator()
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    await db.connect()
    logger.info("Database connected")
    
    # Create admin token if it doesn't exist
    admin_token = await db.get_admin_token()
    if not admin_token:
        token = secrets.token_urlsafe(32)
        await db.create_token(token, is_admin=True)
        logger.info(f"Created admin token: {token}")
    else:
        logger.info("Admin token already exists")
    
    yield
    
    # Shutdown
    await db.close()
    logger.info("Database connection closed")

app = FastAPI(
    title="Image Moderation API",
    description="Automatically detect and block harmful imagery",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Validate bearer token and return token string"""
    token = credentials.credentials
    
    # Verify token exists in database
    token_doc = await db.get_token(token)
    if not token_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Record usage
    await db.record_usage(token, "api_call")
    
    return token

async def get_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Validate admin bearer token"""
    token = credentials.credentials
    # Verify token exists and is admin
    token_doc = await db.get_token(token)
    if not token_doc or not token_doc.get("isAdmin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Record usage
    await db.record_usage(token, "admin_call")
    
    return token

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Image Moderation API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        await db.ping()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Authentication Endpoints (Admin-Only)
@app.post("/auth/tokens", response_model=TokenResponse)
async def create_token(
    token_data: TokenCreate,
    _: str = Depends(get_admin_token)
):
    """Create a new bearer token"""
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Store in database
    await db.create_token(token, token_data.is_admin)
    
    return TokenResponse(
        token=token,
        is_admin=token_data.is_admin,
        created_at=datetime.utcnow()
    )

@app.get("/auth/tokens", response_model=List[dict])
async def list_tokens(_: str = Depends(get_admin_token)):
    """List all bearer tokens"""
    tokens = await db.list_tokens()
    return tokens

@app.delete("/auth/tokens/{token}")
async def delete_token(
    token: str,
    _: str = Depends(get_admin_token)
):
    """Delete a bearer token"""
    success = await db.delete_token(token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    return {"message": "Token deleted successfully"}

# Moderation Endpoint
@app.post("/moderate", response_model=ModerationResult)
async def moderate_image(
    file: UploadFile = File(...),
    token: str = Depends(get_current_token)
):
    """Analyze uploaded image for harmful content"""
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed"
        )
    
    # Check file size (10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10MB"
        )
    
    try:
        # Validate image
        image = Image.open(io.BytesIO(contents))
        image.verify()
        
        # Re-open for processing (verify() closes the image)
        image = Image.open(io.BytesIO(contents))
        
        # Generate image hash for tracking
        image_hash = hashlib.sha256(contents).hexdigest()
        
        # Perform moderation
        result = await image_moderator.moderate_image(image, image_hash)
        
        # Record detailed usage
        await db.record_usage(
            token, 
            "moderate_image",
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(contents),
                "image_hash": image_hash,
                "is_safe": result.is_safe
            }
        )
        
        logger.info(f"Image moderation completed: {image_hash}, safe: {result.is_safe}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )

@app.get("/usage/{token}")
async def get_usage_stats(
    token: str,
    limit: int = 100,
    current_token: str = Depends(get_current_token)
):
    """Get usage statistics for a token (users can only see their own usage)"""
    
    # Users can only see their own usage, admins can see any
    token_doc = await db.get_token(current_token)
    if token != current_token and not token_doc.get("isAdmin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own usage statistics"
        )
    
    usage_records = await db.get_usage_stats(token, limit)
    return {
        "token": token,
        "usage_count": len(usage_records),
        "records": usage_records
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )