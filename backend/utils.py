"""
Utility Functions for Embryo Fragmentation Analysis
File: utils.py
Location: G:\garba\deployment_new\utils.py
"""

import cv2
import numpy as np
import io
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from config import settings


# ============================================
# IMAGE PREPROCESSING
# ============================================

def preprocess_embryo_image(image):
    """
    Enhanced preprocessing for embryo images using CLAHE and denoising
    
    Args:
        image: Input image in BGR format (from OpenCV)
    
    Returns:
        Enhanced image in BGR format
    """
    try:
        # Convert to LAB color space for better contrast enhancement
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels back
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        return denoised
    except Exception as e:
        print(f"Warning: Preprocessing failed, using original image: {e}")
        return image


# ============================================
# QUALITY SCORING
# ============================================

def calculate_quality_score(grade_number: int, confidence: float) -> float:
    """
    Calculate overall quality score combining grade and confidence
    
    Formula: (normalized_grade * 0.7 + confidence * 0.3) * 100
    
    Args:
        grade_number: Grade value (2=C, 3=B, 4=A)
        confidence: Model confidence score (0-1)
    
    Returns:
        Quality score from 0-100
    """
    # Normalize grade to 0-1 scale
    normalized_grade = (grade_number - 2) / 2
    
    # Ensure values are in valid range
    normalized_grade = max(0, min(1, normalized_grade))
    confidence = max(0, min(1, confidence))
    
    # Weighted combination (70% grade, 30% confidence)
    quality_score = (normalized_grade * 0.7 + confidence * 0.3) * 100
    
    return round(quality_score, 2)


# ============================================
# IMAGE VALIDATION (FIXED)
# ============================================

def validate_image(image_bytes) -> tuple:
    """
    Validate uploaded image file
    
    Checks:
    - File size (max 10MB)
    - Image format (JPEG, PNG, TIFF, BMP)
    - Image dimensions (flexible)
    
    Args:
        image_bytes: Image file as bytes
    
    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    # Check file size
    if len(image_bytes) > settings.MAX_UPLOAD_SIZE:
        size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        return False, f"Image too large. Maximum size: {size_mb}MB"
    
    if len(image_bytes) < 1024:  # Less than 1KB
        return False, "Image too small or corrupted"
    
    # Check image format and dimensions
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Check format
        valid_formats = ['JPEG', 'JPG', 'PNG', 'TIFF', 'BMP']
        if image.format not in valid_formats:
            return False, f"Unsupported format: {image.format}. Use JPEG, PNG, or TIFF"
        
        # Check dimensions
        width, height = image.size
        
        # Check total pixels
        total_pixels = width * height
        
        if total_pixels < 5000:
            return False, f"Image too small ({width}x{height}). Minimum area: 5000 pixels"
        
        if width > 10000 or height > 10000:
            return False, f"Image dimensions too large ({width}x{height}). Maximum: 10000x10000 pixels"
        
        # Check aspect ratio
        aspect_ratio = max(width, height) / min(width, height)
        if aspect_ratio > 20:
            return False, f"Image aspect ratio too extreme ({width}x{height}). Max ratio: 20:1"
        
        # Verify image can be read
        image.verify()
        
        return True, "Valid image"
        
    except Exception as e:
        return False, f"Invalid or corrupted image: {str(e)}"


# ============================================
# REPORT GENERATION
# ============================================

def generate_pdf_report(records, patient_id: str) -> bytes:
    """
    Generate comprehensive PDF report for a patient
    
    Args:
        records: List of EmbryoRecord objects from database
        patient_id: Patient identifier
    
    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # ===== TITLE =====
    title = Paragraph(
        f"Embryo Fragmentation Analysis Report<br/>Patient ID: {patient_id}", 
        title_style
    )
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # ===== SUMMARY STATISTICS =====
    if not records:
        elements.append(Paragraph("No embryo records found for this patient.", styles['Normal']))
    else:
        # Calculate statistics
        total_embryos = len(records)
        avg_frag = sum(r.fragmentation_percentage for r in records if r.fragmentation_percentage) / total_embryos
        avg_grade = sum(r.grade for r in records) / total_embryos
        grade_a_count = sum(1 for r in records if r.grade >= 4)
        grade_b_count = sum(1 for r in records if r.grade == 3)
        grade_c_count = sum(1 for r in records if r.grade == 2)
        
        summary_data = [
            ['Report Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Total Embryos Analyzed:', str(total_embryos)],
            ['Average Fragmentation:', f"{avg_frag:.2f}%"],
            ['Average Grade:', f"{avg_grade:.1f}"],
            ['Grade A (Excellent):', f"{grade_a_count} ({grade_a_count/total_embryos*100:.0f}%)"],
            ['Grade B (Acceptable):', f"{grade_b_count} ({grade_b_count/total_embryos*100:.0f}%)"],
            ['Grade C (Poor):', f"{grade_c_count} ({grade_c_count/total_embryos*100:.0f}%)"],
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # ===== DETAILED RESULTS TABLE =====
        elements.append(Paragraph("Detailed Embryo Analysis", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Map grades to letters
        grade_map = {4: 'A', 3: 'B', 2: 'C'}
        
        data = [['Embryo ID', 'Grade', 'Fragmentation %', 'Quality Score', 'Date']]
        for record in records:
            data.append([
                str(record.id),
                grade_map.get(record.grade, str(record.grade)),
                f"{record.fragmentation_percentage:.1f}%" if record.fragmentation_percentage else "N/A",
                f"{record.quality_score:.1f}/100" if record.quality_score else "N/A",
                record.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        results_table = Table(data, colWidths=[1*inch, 0.8*inch, 1.3*inch, 1.3*inch, 1.5*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(results_table)
        
        # ===== GRADING EXPLANATION =====
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("Grading System", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        grading_text = """
        <b>Grade A (≤10% fragmentation):</b> Excellent quality. High implantation potential.<br/>
        <b>Grade B (10-25% fragmentation):</b> Acceptable quality. Moderate implantation potential.<br/>
        <b>Grade C (>25% fragmentation):</b> Poor quality. Lower implantation potential.<br/>
        <br/>
        <i>Note: This analysis is AI-assisted. Please consult with your fertility specialist 
        for clinical decisions.</i>
        """
        elements.append(Paragraph(grading_text, styles['Normal']))
    
    # ===== FOOTER =====
    elements.append(Spacer(1, 0.5*inch))
    footer_text = f"""
    <para align=center>
    <font size=9 color="#7f8c8d">
    <b>Embryo Fragmentation Analysis System</b><br/>
    Powered by YOLOv8 Deep Learning Model<br/>
    <br/>
    This report is for informational purposes only.<br/>
    Please consult with medical professionals for clinical decisions.<br/>
    <br/>
    Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
    </font>
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================
# EMAIL NOTIFICATION (PLACEHOLDER)
# ============================================

def send_email_notification(patient_id: str, embryo_id: int, grade: int, fragmentation: float):
    """
    Send email notification about embryo analysis
    
    Args:
        patient_id: Patient identifier
        embryo_id: Embryo record ID
        grade: Embryo grade (2-4)
        fragmentation: Fragmentation percentage
    """
    if not settings.ENABLE_EMAIL_NOTIFICATIONS:
        print(f"📧 Email notification skipped (disabled in settings)")
        return
    
    # Placeholder - implement email sending here
    print(f"📧 Email notification:")
    print(f"   Patient: {patient_id}")
    print(f"   Embryo ID: {embryo_id}")
    print(f"   Grade: {grade}")
    print(f"   Fragmentation: {fragmentation:.1f}%")


# ============================================
# AUDIT LOGGING
# ============================================

def log_activity(db, endpoint: str, method: str, center_id: str = None, 
                patient_id: str = None, status_code: int = 200, 
                response_time_ms: float = 0):
    """
    Log API activity to audit trail
    
    Args:
        db: Database session
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        center_id: Center identifier (optional)
        patient_id: Patient identifier (optional)
        status_code: HTTP status code
        response_time_ms: Response time in milliseconds
    """
    if not settings.ENABLE_AUDIT_LOGGING:
        return
    
    try:
        from models import AuditLog
        
        log = AuditLog(
            endpoint=endpoint,
            method=method,
            center_id=center_id,
            patient_id=patient_id,
            status_code=status_code,
            response_time_ms=response_time_ms
        )
        
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"⚠️ Audit logging failed: {e}")


# ============================================
# DATA EXPORT
# ============================================

def export_to_excel(records, filename: str) -> str:
    """
    Export embryo records to Excel file
    
    Args:
        records: List of EmbryoRecord objects
        filename: Output filename (without path)
    
    Returns:
        Full path to created Excel file
    """
    import os
    
    # Prepare data
    data = []
    grade_map = {4: 'A', 3: 'B', 2: 'C'}
    
    for record in records:
        data.append({
            'Embryo ID': record.id,
            'Patient ID': record.patient_id,
            'Center ID': record.center_id,
            'Grade': grade_map.get(record.grade, record.grade),
            'Fragmentation %': record.fragmentation_percentage,
            'Embryo Area': record.embryo_area,
            'Fragment Area': record.fragment_area,
            'Confidence': record.confidence_score,
            'Quality Score': record.quality_score,
            'Date': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Notes': record.notes or ''
        })
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    filepath = os.path.join(settings.REPORT_DIR, filename)
    
    with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Embryo Records', index=False)
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Embryo Records']
        
        # Add formatting
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#2c3e50',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        # Format headers
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Auto-adjust column widths
        for i, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            ) + 2
            worksheet.set_column(i, i, max_length)
    
    return filepath


# ============================================
# STATISTICS CALCULATION
# ============================================

def calculate_statistics(records):
    """
    Calculate comprehensive statistics from embryo records
    
    Args:
        records: List of EmbryoRecord objects
    
    Returns:
        Dictionary with statistical metrics
    """
    if not records:
        return {
            'total_count': 0,
            'message': 'No records available'
        }
    
    grades = [r.grade for r in records]
    confidences = [r.confidence_score for r in records]
    fragmentations = [r.fragmentation_percentage for r in records if r.fragmentation_percentage]
    quality_scores = [r.quality_score for r in records if r.quality_score]
    
    stats = {
        'total_count': len(records),
        'grade_mean': round(sum(grades) / len(grades), 2),
        'grade_median': sorted(grades)[len(grades) // 2],
        'grade_mode': max(set(grades), key=grades.count),
        'confidence_mean': round(sum(confidences) / len(confidences), 3),
        'confidence_min': round(min(confidences), 3),
        'confidence_max': round(max(confidences), 3),
        'grade_distribution': {g: grades.count(g) for g in set(grades)},
        'high_quality_count': len([r for r in records if r.grade >= 4]),
        'acceptable_count': len([r for r in records if r.grade == 3]),
        'poor_quality_count': len([r for r in records if r.grade == 2]),
    }
    
    if fragmentations:
        stats['fragmentation_mean'] = round(sum(fragmentations) / len(fragmentations), 2)
        stats['fragmentation_min'] = round(min(fragmentations), 2)
        stats['fragmentation_max'] = round(max(fragmentations), 2)
    
    if quality_scores:
        stats['quality_mean'] = round(sum(quality_scores) / len(quality_scores), 2)
    
    # Best and worst embryos
    if records:
        stats['best_embryo_id'] = max(records, key=lambda r: r.quality_score if r.quality_score else 0).id
        stats['worst_embryo_id'] = min(records, key=lambda r: r.quality_score if r.quality_score else 100).id
    
    return stats


# ============================================
# HELPER FUNCTIONS
# ============================================

def format_response(data, success=True, message=None):
    """
    Format standard API response
    
    Args:
        data: Response data
        success: Success status
        message: Optional message
    
    Returns:
        Formatted response dictionary
    """
    return {
        'success': success,
        'message': message,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }


def get_grade_letter(grade_number: int) -> str:
    """
    Convert grade number to letter
    
    Args:
        grade_number: Grade (2, 3, or 4)
    
    Returns:
        Grade letter (C, B, or A)
    """
    grade_map = {4: 'A', 3: 'B', 2: 'C'}
    return grade_map.get(grade_number, 'Unknown')


def get_recommendation(fragmentation_pct: float) -> str:
    """
    Get recommendation based on fragmentation percentage
    
    Args:
        fragmentation_pct: Fragmentation percentage
    
    Returns:
        Recommendation string
    """
    if fragmentation_pct <= settings.GRADE_A_THRESHOLD:
        return "EXCELLENT - High implantation potential. Recommended for transfer."
    elif fragmentation_pct <= settings.GRADE_B_THRESHOLD:
        return "ACCEPTABLE - Moderate quality. Consider for transfer with caution."
    else:
        return "POOR QUALITY - High fragmentation. Not recommended for transfer."