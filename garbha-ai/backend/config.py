"""
Configuration Management
File: config.py
Location: G:\garba\deployment_new\config.py
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database Configuration
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "admin123"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "embryo_db"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Model Configuration
    MODEL_PATH: str = r"G:\garba\deployment_new\models\best.pt"
    MODEL_VERSION: str = "YOLOv8m-seg-v1.0"
    INPUT_SIZE: int = 640
    NUM_CLASSES: int = 2  # Embryo and Fragments
    
    # Confidence thresholds
    CONF_THRESHOLD: float = 0.15
    IOU_THRESHOLD: float = 0.3
    
    # Application Configuration
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG_MODE: bool = True
    API_TITLE: str = "Embryo Fragmentation Analysis API"
    API_VERSION: str = "2.0.0"
    
    # Security
    SECRET_KEY: str = "embryo-fragmentation-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Storage Configuration
    UPLOAD_DIR: str = r"G:\garba\deployment_new\uploads"
    BACKUP_DIR: str = r"G:\garba\deployment_new\backups"
    LOG_DIR: str = r"G:\garba\deployment_new\logs"
    REPORT_DIR: str = r"G:\garba\deployment_new\reports"
    
    # Performance Settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    BATCH_SIZE: int = 16
    CACHE_TIMEOUT: int = 300  # 5 minutes
    
    # Feature Flags
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    ENABLE_AUDIT_LOGGING: bool = True
    ENABLE_RATE_LIMITING: bool = False
    ENABLE_AUTHENTICATION: bool = False
    
    # Fragmentation Grading Thresholds
    GRADE_A_THRESHOLD: float = 10.0  # ≤10% fragmentation = Grade A
    GRADE_B_THRESHOLD: float = 25.0  # 10-25% fragmentation = Grade B
    # >25% fragmentation = Grade C
    
    # Monitoring
    ENABLE_METRICS: bool = True
    
    class Config:
        env_file = r"G:\garba\deployment_new\.env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Create necessary directories
for directory in [settings.UPLOAD_DIR, settings.BACKUP_DIR, 
                  settings.LOG_DIR, settings.REPORT_DIR]:
    os.makedirs(directory, exist_ok=True)

print("✅ Configuration loaded successfully")
print(f"📍 Database: {settings.DB_NAME}")
print(f"📍 Model: {settings.MODEL_PATH}")