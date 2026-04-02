"""
Pydantic Schemas for API Request/Response Validation
File: schemas.py
Location: G:\garba\deployment_new\schemas.py
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List
from datetime import datetime


class EmbryoCreate(BaseModel):
    """Schema for creating a new embryo record"""
    patient_id: str = Field(..., min_length=1, max_length=100, description="Patient identifier")
    center_id: str = Field(..., min_length=1, max_length=100, description="Hospital/Center identifier")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('patient_id', 'center_id')
    @classmethod
    def validate_ids(cls, v):
        """Validate and standardize IDs"""
        if not v or len(v) > 100:
            raise ValueError('ID must be between 1 and 100 characters')
        return v.upper()


class EmbryoResponse(BaseModel):
    """Basic response schema for embryo record"""
    embryo_id: int = Field(..., description="Unique embryo record ID")
    patient_id: str = Field(..., description="Patient identifier")
    center_id: str = Field(..., description="Hospital/Center identifier")
    grade: int = Field(..., description="Embryo grade (2=C, 3=B, 4=A)")
    confidence_score: float = Field(..., description="Model confidence (0-1)")
    quality_score: Optional[float] = Field(None, description="Overall quality score (0-100)")
    created_at: datetime = Field(..., description="Timestamp of analysis")
    
    class Config:
        from_attributes = True


class EmbryoDetailResponse(BaseModel):
    """Detailed response schema with fragmentation data"""
    embryo_id: int = Field(..., description="Unique embryo record ID")
    patient_id: str = Field(..., description="Patient identifier")
    center_id: str = Field(..., description="Hospital/Center identifier")
    grade: int = Field(..., description="Embryo grade (2=C, 3=B, 4=A)")
    confidence_score: float = Field(..., description="Model confidence (0-1)")
    quality_score: Optional[float] = Field(None, description="Overall quality score (0-100)")
    fragmentation_percentage: Optional[float] = Field(None, description="Fragmentation percentage")
    created_at: datetime = Field(..., description="Timestamp of analysis")
    image_size: Optional[str] = Field(None, description="Original image dimensions")
    notes: Optional[str] = Field(None, description="Additional notes")
    heatmap_available: bool = Field(True, description="Whether heatmap visualization is available")
    
    class Config:
        from_attributes = True


class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions"""
    total_images: int = Field(..., description="Total number of images processed")
    successful: int = Field(..., description="Number of successful predictions")
    failed: int = Field(..., description="Number of failed predictions")
    average_grade: Optional[float] = Field(None, description="Average grade across all embryos")
    average_fragmentation: Optional[float] = Field(None, description="Average fragmentation %")
    best_embryo: Optional[Dict] = Field(None, description="Best quality embryo details")
    results: List[Dict] = Field(..., description="Individual prediction results")


class StatisticsResponse(BaseModel):
    """Response schema for center/patient statistics"""
    center_id: str = Field(..., description="Center identifier")
    period_days: int = Field(..., description="Time period in days")
    total_embryos: int = Field(..., description="Total embryos analyzed")
    grade_distribution: Dict[int, int] = Field(..., description="Distribution of grades")
    average_grade: float = Field(..., description="Average grade")
    average_confidence: float = Field(..., description="Average model confidence")
    average_quality_score: float = Field(..., description="Average quality score")
    average_fragmentation: Optional[float] = Field(None, description="Average fragmentation %")
    high_quality_count: int = Field(..., description="Number of high quality embryos (Grade A)")
    high_quality_percentage: float = Field(..., description="Percentage of high quality embryos")


class HealthCheckResponse(BaseModel):
    """Response schema for health check endpoint"""
    status: str = Field(..., description="Overall system status")
    model_loaded: bool = Field(..., description="Whether YOLOv8 model is loaded")
    database: str = Field(..., description="Database connection status")
    device: str = Field(..., description="Computation device (cpu/cuda)")
    timestamp: str = Field(..., description="Current timestamp")


class DashboardData(BaseModel):
    """Response schema for dashboard data"""
    overview: Dict = Field(..., description="Overview statistics")
    grade_distribution: Dict = Field(..., description="Grade distribution across all records")
    recent_predictions: List[Dict] = Field(..., description="Recent predictions (last 24h)")


class ErrorResponse(BaseModel):
    """Standard error response schema"""
    success: bool = Field(False, description="Success status")
    error: str = Field(..., description="Error type")
    detail: Optional[str] = Field(None, description="Detailed error message")
    timestamp: str = Field(..., description="Error timestamp")


class SuccessResponse(BaseModel):
    """Standard success response schema"""
    success: bool = Field(True, description="Success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict] = Field(None, description="Response data")
    timestamp: str = Field(..., description="Response timestamp")


class PatientInfoCreate(BaseModel):
    """Schema for creating patient information"""
    patient_id: str = Field(..., description="Patient identifier")
    age: Optional[int] = Field(None, ge=18, le=100, description="Patient age")
    treatment_cycle: Optional[int] = Field(None, ge=1, description="Current treatment cycle")
    previous_ivf_cycles: Optional[int] = Field(None, ge=0, description="Number of previous IVF cycles")
    has_genetic_screening: bool = Field(False, description="Whether genetic screening was done")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")


class CenterInfoCreate(BaseModel):
    """Schema for creating center/hospital information"""
    center_id: str = Field(..., description="Center identifier")
    center_name: str = Field(..., description="Center/Hospital name")
    location: Optional[str] = Field(None, description="Center location")
    contact_email: Optional[str] = Field(None, description="Center contact email")
    contact_phone: Optional[str] = Field(None, description="Center contact phone")
    subscription_tier: str = Field("basic", description="Subscription tier (basic/premium/enterprise)")


class ReportRequest(BaseModel):
    """Schema for report generation request"""
    patient_id: str = Field(..., description="Patient identifier")
    format: str = Field("pdf", pattern="^(pdf|excel|json)$", description="Report format")
    include_heatmaps: bool = Field(True, description="Include heatmap visualizations")
    include_statistics: bool = Field(True, description="Include statistical analysis")


class PredictionDetail(BaseModel):
    """Detailed prediction information"""
    embryo_id: int
    grade: int
    grade_letter: str  # A, B, or C
    fragmentation_percentage: float
    embryo_area: int
    fragment_area: int
    confidence_score: float
    quality_score: float
    recommendation: str
    timestamp: datetime
    
    class Config:
        from_attributes = True