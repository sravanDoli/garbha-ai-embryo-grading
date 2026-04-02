"""
Database Initialization Script
File: init_database.py
Location: G:\garba\deployment_new\init_database.py

This script will:
1. Test database connection
2. Create all tables automatically
3. Add sample model version record
4. Verify setup

Run this ONCE after setting up all files
"""

import sys
import os
from sqlalchemy import text

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print(" EMBRYO FRAGMENTATION SYSTEM - DATABASE INITIALIZATION")
print("=" * 70)
print()

# Step 1: Test imports
print("Step 1: Testing imports...")
try:
    from database import Base, engine, SessionLocal, DATABASE_URL
    from models import (EmbryoRecord, PredictionHistory, ModelVersion, 
                       AuditLog, PatientInfo, CenterInfo)
    from config import settings
    print("✅ All imports successful")
    print(f"📍 Database URL: {DATABASE_URL}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

print()

# Step 2: Test database connection
print("Step 2: Testing database connection...")
try:
    db = SessionLocal()
    db.execute(text("SELECT 1"))
    db.close()
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print()
    print("💡 Troubleshooting:")
    print("   1. Make sure PostgreSQL is running")
    print("   2. Check if 'embryo_db' database exists")
    print("   3. Verify credentials in config.py")
    print("   4. Try running: psql -U postgres -d embryo_db")
    sys.exit(1)

print()

# Step 3: Create all tables
print("Step 3: Creating database tables...")
print("   This will automatically create:")
print("   • embryo_records")
print("   • prediction_history")
print("   • model_versions")
print("   • audit_logs")
print("   • patient_info")
print("   • center_info")
print()

try:
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
except Exception as e:
    print(f"❌ Table creation failed: {e}")
    sys.exit(1)

print()

# Step 4: Verify tables were created
print("Step 4: Verifying tables...")
try:
    db = SessionLocal()
    
    # Check each table
    tables_to_check = [
        ('embryo_records', EmbryoRecord),
        ('prediction_history', PredictionHistory),
        ('model_versions', ModelVersion),
        ('audit_logs', AuditLog),
        ('patient_info', PatientInfo),
        ('center_info', CenterInfo)
    ]
    
    for table_name, model_class in tables_to_check:
        count = db.query(model_class).count()
        print(f"   ✅ {table_name}: {count} records")
    
    db.close()
    print("✅ All tables verified")
except Exception as e:
    print(f"❌ Table verification failed: {e}")
    sys.exit(1)

print()

# Step 5: Add initial model version record
print("Step 5: Adding model version record...")
try:
    db = SessionLocal()
    
    # Check if model version already exists
    existing = db.query(ModelVersion).filter_by(
        version_name=settings.MODEL_VERSION
    ).first()
    
    if existing:
        print(f"   ℹ Model version '{settings.MODEL_VERSION}' already exists")
    else:
        model_version = ModelVersion(
            version_name=settings.MODEL_VERSION,
            model_path=settings.MODEL_PATH,
            description="YOLOv8m Segmentation model for embryo fragmentation analysis",
            is_active=True
        )
        db.add(model_version)
        db.commit()
        print(f"   ✅ Added model version: {settings.MODEL_VERSION}")
    
    db.close()
except Exception as e:
    print(f"❌ Model version creation failed: {e}")
    sys.exit(1)

print()

# Step 6: Show database schema
print("Step 6: Database schema created:")
print()
print("┌─────────────────────────────────────────────────────────────────┐")
print("│ EMBRYO_RECORDS Table                                            │")
print("├─────────────────────────────────────────────────────────────────┤")
print("│ • id (Primary Key)                                              │")
print("│ • patient_id                                                    │")
print("│ • center_id                                                     │")
print("│ • grade (2=C, 3=B, 4=A)                                         │")
print("│ • confidence_score                                              │")
print("│ • quality_score                                                 │")
print("│ • fragmentation_percentage                                      │")
print("│ • embryo_area, fragment_area                                    │")
print("│ • heatmap_data (binary)                                         │")
print("│ • created_at, updated_at                                        │")
print("└─────────────────────────────────────────────────────────────────┘")
print()

# Step 7: Final summary
print("=" * 70)
print(" ✅ DATABASE INITIALIZATION COMPLETE!")
print("=" * 70)
print()
print("📊 Summary:")
print(f"   • Database: {settings.DB_NAME}")
print(f"   • Host: {settings.DB_HOST}:{settings.DB_PORT}")
print(f"   • Tables created: 6")
print(f"   • Model: {settings.MODEL_VERSION}")
print()
print("🚀 Next Steps:")
print("   1. Copy your best.pt file to: G:/garba/deployment_new/models/")
print("   2. Run: python main.py")
print("   3. Or double-click: run_server.bat")
print("   4. Access API: http://localhost:8000/docs")
print()
print("=" * 70)
