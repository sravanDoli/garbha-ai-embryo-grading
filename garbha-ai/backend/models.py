"""
Database Models for Embryo Fragmentation System
File: models.py
Location: G:\garba\deployment_new\models.py
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class EmbryoRecord(Base):
    """Main embryo record with fragmentation analysis"""
    __tablename__ = "embryo_records"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(String(100), index=True, nullable=False)
    center_id = Column(String(100), index=True, nullable=False)
    
    # Grading information
    grade = Column(Integer, nullable=False)
    confidence_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    
    # Fragmentation metrics
    fragmentation_percentage = Column(Float, nullable=True)
    embryo_area = Column(Integer, nullable=True)
    fragment_area = Column(Integer, nullable=True)
    
    # Image information
    heatmap_data = Column(LargeBinary, nullable=True)
    image_size = Column(String(50), nullable=True)
    
    # Additional metadata
    notes = Column(Text, nullable=True)
    device_used = Column(String(50), nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<EmbryoRecord(id={self.id}, patient={self.patient_id}, grade={self.grade})>"


class PredictionHistory(Base):
    """Track prediction history"""
    __tablename__ = "prediction_history"
    
    id = Column(Integer, primary_key=True, index=True)
    embryo_id = Column(Integer, ForeignKey('embryo_records.id'), nullable=False)
    
    # Model information
    model_version = Column(String(50), nullable=True)
    predicted_grade = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    fragmentation_pct = Column(Float, nullable=True)
    
    # Re-prediction flag
    is_reanalysis = Column(Boolean, default=False)
    previous_grade = Column(Integer, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PredictionHistory(embryo_id={self.embryo_id}, grade={self.predicted_grade})>"


class ModelVersion(Base):
    """Track different YOLOv8 model versions"""
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String(100), unique=True, nullable=False)
    model_path = Column(String(500), nullable=False)
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    map50 = Column(Float, nullable=True)
    map50_95 = Column(Float, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    training_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ModelVersion(name={self.version_name}, active={self.is_active})>"


class AuditLog(Base):
    """Audit trail for all API activities"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Request information
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    user_ip = Column(String(50), nullable=True)
    
    # User/Center identification
    center_id = Column(String(100), nullable=True)
    patient_id = Column(String(100), nullable=True)
    
    # Response information
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    
    # Additional context
    error_message = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AuditLog(endpoint={self.endpoint}, status={self.status_code})>"


class PatientInfo(Base):
    """Store patient demographic information"""
    __tablename__ = "patient_info"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Demographics
    age = Column(Integer, nullable=True)
    treatment_cycle = Column(Integer, nullable=True)
    
    # Medical history flags
    previous_ivf_cycles = Column(Integer, nullable=True)
    has_genetic_screening = Column(Boolean, default=False)
    
    # Contact information
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Timestamps
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PatientInfo(patient_id={self.patient_id})>"


class CenterInfo(Base):
    """Store hospital/center information"""
    __tablename__ = "center_info"
    
    id = Column(Integer, primary_key=True, index=True)
    center_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Center details
    center_name = Column(String(200), nullable=False)
    location = Column(String(200), nullable=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Subscription info
    subscription_tier = Column(String(50), default="basic")
    api_key = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Usage limits
    monthly_prediction_limit = Column(Integer, default=1000)
    current_month_usage = Column(Integer, default=0)
    
    # Timestamps
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CenterInfo(center_id={self.center_id}, name={self.center_name})>"