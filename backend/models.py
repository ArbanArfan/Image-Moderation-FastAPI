# models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional

class TokenCreate(BaseModel):
    """Request model for creating a new token"""
    is_admin: bool = Field(default=False, description="Whether the token has admin privileges")

class TokenResponse(BaseModel):
    """Response model for token creation"""
    token: str = Field(description="The generated bearer token")
    is_admin: bool = Field(description="Whether the token has admin privileges")
    created_at: datetime = Field(description="When the token was created")

class ModerationCategory(BaseModel):
    """Individual moderation category result"""
    name: str = Field(description="Category name (e.g., 'violence', 'nudity')")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score (0-1)")
    detected: bool = Field(description="Whether harmful content was detected in this category")

class ModerationResult(BaseModel):
    """Result of image moderation analysis"""
    is_safe: bool = Field(description="Overall safety determination")
    risk_score: float = Field(ge=0.0, le=1.0, description="Overall risk score (0-1, higher is riskier)")
    categories: List[ModerationCategory] = Field(description="Individual category results")
    image_hash: str = Field(description="SHA256 hash of the analyzed image")
    analyzed_at: datetime = Field(description="When the analysis was performed")
    processing_time_ms: int = Field(description="Processing time in milliseconds")

class UsageRecord(BaseModel):
    """Usage tracking record"""
    token: str = Field(description="Token that made the request")
    endpoint: str = Field(description="API endpoint accessed")
    timestamp: datetime = Field(description="When the request was made")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional request metadata")

class UsageStats(BaseModel):
    """Usage statistics summary"""
    token: str = Field(description="Token identifier")
    total_usage: int = Field(description="Total number of API calls")
    last_used: Optional[datetime] = Field(description="Last usage timestamp")
    endpoint_breakdown: Dict[str, int] = Field(description="Usage count by endpoint")

class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field(description="Overall system status")
    database: str = Field(description="Database connection status")
    timestamp: str = Field(description="Health check timestamp")

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(description="Error message")
    error_code: Optional[str] = Field(default=None, description="Specific error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")