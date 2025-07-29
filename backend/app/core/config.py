"""
Core configuration settings for the Manufacturing RFQ Platform
"""
import os
from typing import List, Optional
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "manufacturing-rfq-platform-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "postgresql://rfq_user:rfq_password@localhost/rfq_platform"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://rfq_user:rfq_password@localhost/rfq_platform"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # File Storage
    UPLOAD_DIRECTORY: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES: List[str] = [
        "dwg", "step", "stp", "iges", "igs", "pdf", "png", "jpg", "jpeg"
    ]
    
    # AWS S3 (Optional)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    USE_S3: bool = False
    
    # AI/ML Configuration
    ML_MODEL_PATH: str = "ml-models"
    ENABLE_GPU: bool = False
    AI_CONFIDENCE_THRESHOLD: float = 0.8
    
    # CAD Processing
    CAD_PROCESSING_TIMEOUT: int = 300  # 5 minutes
    ENABLE_3D_VIEWER: bool = True
    
    # Email Configuration (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: str = "RFQ Platform"
    
    # Business Logic
    DEFAULT_LABOR_RATE: float = 75.0  # per hour
    DEFAULT_MATERIAL_MARKUP: float = 1.2  # 20% markup
    DEFAULT_OVERHEAD_RATE: float = 0.15  # 15% overhead
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)