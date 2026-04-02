"""
Complete FastAPI Application for Embryo Fragmentation Analysis
Using YOLOv8 Segmentation Model
Location: G:\garba\deployment_new\main.py
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
import torch
import numpy as np
import cv2
from PIL import Image
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from ultralytics import YOLO
import tempfile
import os

from database import engine, SessionLocal, Base
from models import EmbryoRecord, PredictionHistory, ModelVersion, AuditLog
from schemas import (EmbryoResponse, BatchPredictionResponse, StatisticsResponse,
                     EmbryoDetailResponse, HealthCheckResponse)
from config import settings
from utils import (calculate_quality_score, generate_pdf_report, 
                   preprocess_embryo_image, validate_image)

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Embryo Fragmentation Analysis API",
    version="2.0.0",
    description="YOLOv8-powered embryo fragmentation quantification system"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced Error Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": str(exc),
            "message": "Please check your input parameters"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    import traceback
    print("UNHANDLED ERROR:", traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "message": "An unexpected error occurred. Check server logs for details."
        }
    )

# ============================================
# LOAD YOLO MODEL
# ============================================

print("🔄 Loading YOLOv8 Segmentation Model...")
try:
    model = YOLO(settings.MODEL_PATH)
    print(f"✅ Model loaded from: {settings.MODEL_PATH}")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🖥️ Using device: {device}")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

# ============================================
# DATABASE DEPENDENCY
# ============================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_fragmentation(masks, classes):
    """Calculate fragmentation percentage from segmentation masks"""
    embryo_mask = None
    fragment_masks = []
    
    for mask, cls in zip(masks, classes):
        if cls == 0:  # Embryo
            if embryo_mask is None:
                embryo_mask = mask
            else:
                embryo_mask = np.logical_or(embryo_mask, mask)
        elif cls == 1:  # Fragments
            fragment_masks.append(mask)
    
    if embryo_mask is None:
        return None
    
    embryo_area = np.sum(embryo_mask)
    
    if len(fragment_masks) > 0:
        combined_fragments = fragment_masks[0]
        for frag in fragment_masks[1:]:
            combined_fragments = np.logical_or(combined_fragments, frag)
        fragment_area = np.sum(combined_fragments)
    else:
        fragment_area = 0
    
    fragmentation_pct = (fragment_area / embryo_area) * 100 if embryo_area > 0 else 0
    
    # Grade assignment
    if fragmentation_pct <= settings.GRADE_A_THRESHOLD:
        grade = "A"
        grade_number = 4
        grade_color = "green"
        recommendation = "EXCELLENT - Proceed to next step"
    elif fragmentation_pct <= settings.GRADE_B_THRESHOLD:
        grade = "B"
        grade_number = 3
        grade_color = "orange"
        recommendation = "ACCEPTABLE - Consider with caution"
    else:
        grade = "C"
        grade_number = 2
        grade_color = "red"
        recommendation = "POOR QUALITY - Not recommended"
    
    return {
        'fragmentation_pct': float(fragmentation_pct),  # Convert to Python float
        'embryo_area': int(embryo_area),
        'fragment_area': int(fragment_area),
        'grade': grade,
        'grade_number': int(grade_number),
        'grade_color': grade_color,
        'recommendation': recommendation
    }


def multi_scale_inference(model, image_path, conf_threshold=0.15):
    """Perform multi-scale inference for better detection"""
    image = cv2.imread(image_path)
    if image is None:
        return None, None
    
    # Try with preprocessing
    enhanced = preprocess_embryo_image(image)
    temp_path = tempfile.mktemp(suffix='.jpg')
    cv2.imwrite(temp_path, enhanced)
    
    # Try multiple confidence thresholds
    best_results = None
    best_count = 0
    
    for conf in [0.10, 0.15, 0.20, 0.25]:
        try:
            results = model(temp_path, conf=conf, iou=0.3, verbose=False)[0]
            
            if results.masks is not None:
                count = len(results.masks)
                if count > best_count:
                    best_count = count
                    best_results = results
        except:
            continue
    
    # Try original if no good results
    if best_results is None or best_count == 0:
        for conf in [0.10, 0.15]:
            try:
                results = model(image_path, conf=conf, iou=0.3, verbose=False)[0]
                if results.masks is not None and len(results.masks) > 0:
                    best_results = results
                    break
            except:
                continue
    
    # Clean up
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return best_results, image


def generate_visualization(image, masks, classes, confidences, metrics):
    """Generate visualization with segmentation masks and results"""
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    
    # Original image
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    axes[0].imshow(image_rgb)
    axes[0].set_title('Original Image', fontsize=14, fontweight='bold')
    axes[0].axis('off')
    
    # Segmentation overlay
    overlay = image_rgb.copy()
    for mask, cls in zip(masks, classes):
        color = np.array([0, 255, 0]) if cls == 0 else np.array([255, 0, 0])
        colored_mask = np.zeros_like(image_rgb)
        for i in range(3):
            colored_mask[:, :, i] = mask * color[i]
        overlay = cv2.addWeighted(overlay, 1, colored_mask, 0.5, 0)
    
    axes[1].imshow(overlay)
    axes[1].set_title('Segmentation Masks\n(Green: Embryo, Red: Fragments)',
                     fontsize=14, fontweight='bold')
    axes[1].axis('off')
    
    # Results text
    axes[2].axis('off')
    result_text = f"""
EMBRYO FRAGMENTATION ANALYSIS
================================

Measurements:
  Embryo Area: {metrics['embryo_area']:,} pixels
  Fragment Area: {metrics['fragment_area']:,} pixels

Fragmentation: {metrics['fragmentation_pct']:.2f}%

GRADE: {metrics['grade']}

================================

Grade Classification:
  Grade A: <=10% fragmentation
  Grade B: 10-25% fragmentation
  Grade C: >25% fragmentation

================================

Recommendation:
  {metrics['recommendation']}

================================

Confidence: {confidences.mean():.1%}
    """
    
    axes[2].text(0.1, 0.5, result_text, fontsize=11, family='monospace',
                verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor=metrics['grade_color'],
                         alpha=0.2, edgecolor=metrics['grade_color'], linewidth=2))
    
    plt.tight_layout()
    
    # Convert to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf.getvalue()

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/", tags=["General"])
async def root():
    return {
        "message": "Embryo Fragmentation Analysis API",
        "version": "2.0.0",
        "model": "YOLOv8-Segmentation",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "predict": "/predict",
            "dashboard": "/dashboard"
        }
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["General"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "database": db_status,
        "device": 'cuda' if torch.cuda.is_available() else 'cpu',
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/predict", tags=["Prediction"])
async def predict_embryo(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    patient_id: str = None,
    center_id: str = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Analyze embryo image and calculate fragmentation"""
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        # Read and validate image
        image_bytes = await image.read()
        is_valid, message = validate_image(image_bytes)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Save temporary file
        temp_path = tempfile.mktemp(suffix='.jpg')
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)
        
        # Perform inference
        results, original_image = multi_scale_inference(model, temp_path)
        
        if results is None or results.masks is None or len(results.masks) == 0:
            # Clean up and raise error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(
                status_code=404, 
                detail="No embryo detected in image. Please ensure image quality and try again."
            )
        
        # Process results
        masks = results.masks.data.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy().astype(int)
        confidences = results.boxes.conf.cpu().numpy()
        
        h, w = original_image.shape[:2]
        resized_masks = []
        for mask in masks:
            resized_mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
            resized_masks.append(resized_mask > 0.5)
        
        # Calculate fragmentation
        metrics = calculate_fragmentation(resized_masks, classes)
        
        if metrics is None:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(status_code=404, detail="No embryo found in detections")
        
        # Calculate quality score
        quality_score = calculate_quality_score(
            metrics['grade_number'], 
            float(confidences.mean())
        )
        
        # Generate visualization
        heatmap_bytes = generate_visualization(
            original_image, resized_masks, classes, confidences, metrics
        )
        
        # ============================================
        # CRITICAL FIX: Convert all NumPy types to Python native types
        # ============================================
        embryo_record = EmbryoRecord(
            patient_id=patient_id.upper() if patient_id else "UNKNOWN",
            center_id=center_id.upper() if center_id else "UNKNOWN",
            grade=int(metrics['grade_number']),
            confidence_score=float(confidences.mean()),
            quality_score=float(quality_score),
            fragmentation_percentage=float(metrics['fragmentation_pct']),  # Convert np.float64
            embryo_area=int(metrics['embryo_area']),  # Convert np.int64
            fragment_area=int(metrics['fragment_area']),  # Convert np.int64
            heatmap_data=heatmap_bytes,
            notes=notes,
            image_size=f"{w}x{h}",
            device_used='cuda' if torch.cuda.is_available() else 'cpu',
            created_at=datetime.utcnow()
        )
        
        db.add(embryo_record)
        db.commit()
        db.refresh(embryo_record)
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        print(f"✅ Saved embryo {embryo_record.id} for patient {embryo_record.patient_id}")
        
        return {
            "embryo_id": embryo_record.id,
            "patient_id": embryo_record.patient_id,
            "center_id": embryo_record.center_id,
            "grade": embryo_record.grade,
            "confidence_score": embryo_record.confidence_score,
            "quality_score": embryo_record.quality_score,
            "fragmentation_percentage": embryo_record.fragmentation_percentage,
            "embryo_area": embryo_record.embryo_area,
            "fragment_area": embryo_record.fragment_area,
            "created_at": embryo_record.created_at.isoformat(),
            "image_size": embryo_record.image_size,
            "notes": embryo_record.notes,
            "heatmap_available": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("ERROR in predict_embryo:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/embryo/{embryo_id}/heatmap", tags=["Embryo"])
async def get_heatmap(embryo_id: int, db: Session = Depends(get_db)):
    """Get visualization heatmap for embryo"""
    try:
        embryo = db.query(EmbryoRecord).filter(EmbryoRecord.id == embryo_id).first()
        
        if not embryo:
            raise HTTPException(status_code=404, detail=f"Embryo with ID {embryo_id} not found")
        
        if not embryo.heatmap_data:
            raise HTTPException(status_code=404, detail="Heatmap not available for this embryo")
        
        return StreamingResponse(
            io.BytesIO(embryo.heatmap_data),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=heatmap_{embryo_id}.png"}
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("ERROR in get_heatmap:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error retrieving heatmap: {str(e)}")


@app.get("/embryo/{embryo_id}", tags=["Embryo"])
async def get_embryo_record(embryo_id: int, db: Session = Depends(get_db)):
    """Get embryo record by ID"""
    try:
        embryo = db.query(EmbryoRecord).filter(EmbryoRecord.id == embryo_id).first()
        
        if not embryo:
            raise HTTPException(
                status_code=404, 
                detail=f"Embryo with ID {embryo_id} not found"
            )
        
        # Return as plain dict to avoid schema issues
        return {
            "embryo_id": embryo.id,
            "patient_id": embryo.patient_id,
            "center_id": embryo.center_id,
            "grade": embryo.grade,
            "confidence_score": embryo.confidence_score or 0,
            "quality_score": embryo.quality_score or 0,
            "fragmentation_percentage": embryo.fragmentation_percentage or 0,
            "embryo_area": embryo.embryo_area or 0,
            "fragment_area": embryo.fragment_area or 0,
            "created_at": embryo.created_at.isoformat() if embryo.created_at else None,
            "image_size": embryo.image_size or "unknown",
            "notes": embryo.notes or ""
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("ERROR in get_embryo_record:", traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving embryo: {str(e)}"
        )


@app.get("/patient/{patient_id}/embryos", tags=["Patient"])
async def get_patient_embryos(patient_id: str, db: Session = Depends(get_db)):
    """Get all embryo records for a patient"""
    try:
        # Convert to uppercase for consistent search
        patient_id_upper = patient_id.upper()
        
        embryos = db.query(EmbryoRecord).filter(
            EmbryoRecord.patient_id == patient_id_upper
        ).order_by(EmbryoRecord.created_at.desc()).all()
        
        if not embryos:
            return {
                "success": False,
                "message": f"No embryos found for patient {patient_id}",
                "patient_id": patient_id_upper,
                "count": 0,
                "embryos": []
            }
        
        # Convert to list of dicts
        results = []
        for embryo in embryos:
            results.append({
                "embryo_id": embryo.id,
                "patient_id": embryo.patient_id,
                "center_id": embryo.center_id,
                "grade": embryo.grade,
                "confidence_score": embryo.confidence_score or 0,
                "fragmentation_percentage": embryo.fragmentation_percentage or 0,
                "quality_score": embryo.quality_score or 0,
                "created_at": embryo.created_at.isoformat() if embryo.created_at else None
            })
        
        return {
            "success": True,
            "patient_id": patient_id_upper,
            "count": len(results),
            "embryos": results
        }
    except Exception as e:
        import traceback
        print("ERROR in get_patient_embryos:", traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving patient embryos: {str(e)}"
        )


@app.get("/center/{center_id}/embryos", tags=["Center"])
async def get_center_embryos(center_id: str, db: Session = Depends(get_db)):
    """Get all embryo records for a center"""
    try:
        # Convert to uppercase for consistent search
        center_id_upper = center_id.upper()
        
        embryos = db.query(EmbryoRecord).filter(
            EmbryoRecord.center_id == center_id_upper
        ).order_by(EmbryoRecord.created_at.desc()).all()
        
        if not embryos:
            return {
                "success": False,
                "message": f"No embryos found for center {center_id}",
                "center_id": center_id_upper,
                "count": 0,
                "embryos": []
            }
        
        # Convert to list of dicts
        results = []
        for embryo in embryos:
            results.append({
                "embryo_id": embryo.id,
                "patient_id": embryo.patient_id,
                "center_id": embryo.center_id,
                "grade": embryo.grade,
                "confidence_score": embryo.confidence_score or 0,
                "fragmentation_percentage": embryo.fragmentation_percentage or 0,
                "quality_score": embryo.quality_score or 0,
                "created_at": embryo.created_at.isoformat() if embryo.created_at else None
            })
        
        return {
            "success": True,
            "center_id": center_id_upper,
            "count": len(results),
            "embryos": results
        }
    except Exception as e:
        import traceback
        print("ERROR in get_center_embryos:", traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving center embryos: {str(e)}"
        )


@app.get("/statistics/{center_id}", tags=["Analytics"])
async def get_center_statistics(
    center_id: str,
    days: Optional[int] = 30,
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a center"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        center_id_upper = center_id.upper()
        
        records = db.query(EmbryoRecord).filter(
            EmbryoRecord.center_id == center_id_upper,
            EmbryoRecord.created_at >= start_date
        ).all()
        
        if not records:
            raise HTTPException(status_code=404, detail=f"No records found for center {center_id}")
        
        # Calculate statistics
        grade_dist = {}
        for record in records:
            grade_dist[record.grade] = grade_dist.get(record.grade, 0) + 1
        
        total = len(records)
        avg_grade = sum(r.grade for r in records) / total
        avg_confidence = sum(r.confidence_score for r in records) / total
        avg_quality = sum(r.quality_score or 0 for r in records) / total
        avg_fragmentation = sum(r.fragmentation_percentage or 0 for r in records) / total
        
        high_quality = len([r for r in records if r.grade >= 4])
        
        return {
            "center_id": center_id_upper,
            "period_days": days,
            "total_embryos": total,
            "grade_distribution": grade_dist,
            "average_grade": round(avg_grade, 2),
            "average_confidence": round(avg_confidence, 3),
            "average_quality_score": round(avg_quality, 2),
            "average_fragmentation": round(avg_fragmentation, 2),
            "high_quality_count": high_quality,
            "high_quality_percentage": round((high_quality / total) * 100, 1)
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print("ERROR in get_center_statistics:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


@app.get("/dashboard", tags=["Analytics"])
async def get_dashboard(db: Session = Depends(get_db)):
    """Get dashboard data"""
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent = db.query(EmbryoRecord).filter(EmbryoRecord.created_at >= yesterday).all()
        
        total_embryos = db.query(func.count(EmbryoRecord.id)).scalar() or 0
        total_patients = db.query(func.count(func.distinct(EmbryoRecord.patient_id))).scalar() or 0
        total_centers = db.query(func.count(func.distinct(EmbryoRecord.center_id))).scalar() or 0
        
        all_records = db.query(EmbryoRecord).all()
        grade_dist = {}
        for record in all_records:
            grade_dist[f"Grade {record.grade}"] = grade_dist.get(f"Grade {record.grade}", 0) + 1
        
        return {
            "overview": {
                "total_embryos": total_embryos,
                "total_patients": total_patients,
                "total_centers": total_centers,
                "recent_predictions_24h": len(recent)
            },
            "grade_distribution": grade_dist,
            "recent_predictions": [
                {
                    "id": r.id,
                    "patient_id": r.patient_id,
                    "grade": r.grade,
                    "fragmentation": r.fragmentation_percentage,
                    "confidence": r.confidence_score,
                    "timestamp": r.created_at.isoformat()
                } for r in recent[:10]
            ]
        }
    except Exception as e:
        import traceback
        print("ERROR in get_dashboard:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
