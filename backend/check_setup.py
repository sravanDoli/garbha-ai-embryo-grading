"""
Setup Verification Script
File: check_setup.py
Location: G:\garba\deployment_new\check_setup.py

Run this script to verify your installation is complete
Usage: python check_setup.py
"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("  Embryo Grading API - Setup Verification")
print("=" * 60)
print()

# Color codes for terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_pass(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def check_fail(msg):
    print(f"{RED}✗{RESET} {msg}")

def check_warn(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def check_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")

# Track results
passed = 0
failed = 0
warnings = 0

print("Checking Python packages...")
print("-" * 60)

# Check required packages
required_packages = [
    'fastapi',
    'uvicorn',
    'sqlalchemy',
    'psycopg2',
    'pydantic',
    'pydantic_settings',
    'torch',
    'torchvision',
    'ultralytics',
    'cv2',
    'PIL',
    'numpy',
    'pandas',
    'matplotlib',
    'plotly',
    'reportlab',
    'python-dotenv'
]

for package in required_packages:
    try:
        if package == 'cv2':
            __import__('cv2')
        elif package == 'PIL':
            __import__('PIL')
        elif package == 'python-dotenv':
            __import__('dotenv')
        elif package == 'pydantic_settings':
            __import__('pydantic_settings')
        else:
            __import__(package)
        check_pass(f"{package:20} - Installed")
        passed += 1
    except ImportError:
        check_fail(f"{package:20} - NOT INSTALLED")
        failed += 1

print()
print("Checking project structure...")
print("-" * 60)

# Check project structure
base_path = Path(r"G:/garba/deployment_new")
required_files = [
    'main.py',
    'database.py',
    'models.py',
    'schemas.py',
    'config.py',
    'utils.py',
]

required_dirs = [
    'models',
    'logs',
    'backups',
    'reports',
    'uploads',
]

for file in required_files:
    filepath = base_path / file
    if filepath.exists():
        check_pass(f"{file:20} - Found")
        passed += 1
    else:
        check_fail(f"{file:20} - Missing")
        failed += 1

print()
for directory in required_dirs:
    dirpath = base_path / directory
    if dirpath.exists():
        check_pass(f"{directory:20} - Found")
        passed += 1
    else:
        check_warn(f"{directory:20} - Missing (will be created)")
        warnings += 1
        # Create missing directory
        dirpath.mkdir(exist_ok=True)

print()
print("Checking model file...")
print("-" * 60)

models_dir = base_path / 'models'
if models_dir.exists():
    pt_files = list(models_dir.glob('*.pt'))
    if pt_files:
        check_pass(f"Found {len(pt_files)} model file(s)")
        for pt_file in pt_files:
            size_mb = pt_file.stat().st_size / (1024 * 1024)
            check_info(f"  - {pt_file.name} ({size_mb:.1f} MB)")
        passed += 1
    else:
        check_fail("No .pt model files found in models/")
        check_info("  Please copy your model.pt file to G:/garba/deployment_new/models/")
        failed += 1
else:
    check_fail("models/ directory not found")
    failed += 1

print()
print("Checking configuration...")
print("-" * 60)

config_file = base_path / 'config.py'
if config_file.exists():
    check_pass("config.py file found")
    
    try:
        from config import settings
        check_pass("Configuration loaded successfully")
        check_info(f"  Database: {settings.DB_NAME}")
        check_info(f"  Model Path: {settings.MODEL_PATH}")
        passed += 1
        
        # Check if model path exists
        if os.path.exists(settings.MODEL_PATH):
            check_pass("Model file found at configured path")
            passed += 1
        else:
            check_fail("Model file NOT found at configured path")
            check_info(f"  Expected: {settings.MODEL_PATH}")
            failed += 1
            
    except Exception as e:
        check_fail(f"Configuration import failed: {e}")
        failed += 1
else:
    check_fail("config.py file not found")
    failed += 1

print()
print("Testing database connection...")
print("-" * 60)

try:
    from database import SessionLocal, engine
    from sqlalchemy import text
    
    db = SessionLocal()
    db.execute(text("SELECT 1"))
    db.close()
    check_pass("Database connection successful")
    passed += 1
except Exception as e:
    check_fail(f"Database connection failed: {str(e)}")
    check_info("  Make sure PostgreSQL is running")
    check_info("  Check if 'embryo_db' database exists")
    check_info("  Verify credentials in config.py")
    failed += 1

print()
print("Testing PyTorch...")
print("-" * 60)

try:
    import torch
    
    check_pass(f"PyTorch version: {torch.__version__}")
    
    if torch.cuda.is_available():
        check_pass(f"CUDA available: {torch.cuda.get_device_name(0)}")
        passed += 1
    else:
        check_warn("CUDA not available (using CPU)")
        check_info("  This is normal if you don't have a GPU")
        warnings += 1
    
    # Test model loading
    try:
        from config import settings
        if Path(settings.MODEL_PATH).exists():
            from ultralytics import YOLO
            model = YOLO(settings.MODEL_PATH)
            check_pass("Model file loads successfully")
            passed += 1
        else:
            check_warn("Model file not found at configured path")
            warnings += 1
    except Exception as e:
        check_fail(f"Model loading failed: {str(e)}")
        failed += 1
        
except Exception as e:
    check_fail(f"PyTorch test failed: {str(e)}")
    failed += 1

print()
print("Checking network ports...")
print("-" * 60)

import socket

def check_port(port, service):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result == 0:
        check_warn(f"Port {port} ({service}) is already in use")
        return False
    else:
        check_pass(f"Port {port} ({service}) is available")
        return True

if check_port(8000, "API Server"):
    passed += 1
else:
    warnings += 1
    check_info("  You may need to stop existing server or use different port")

if check_port(5432, "PostgreSQL"):
    check_info("  PostgreSQL may not be running (this is ok if using remote DB)")
else:
    check_pass("PostgreSQL is running on default port")
    passed += 1

print()
print("=" * 60)
print("  VERIFICATION SUMMARY")
print("=" * 60)
print()
print(f"{GREEN}Passed:   {passed}{RESET}")
print(f"{RED}Failed:   {failed}{RESET}")
print(f"{YELLOW}Warnings: {warnings}{RESET}")
print()

if failed == 0:
    print(f"{GREEN}{'=' * 60}{RESET}")
    print(f"{GREEN}All checks passed! You're ready to go!{RESET}")
    print(f"{GREEN}{'=' * 60}{RESET}")
    print()
    print("Next steps:")
    print("  1. Double-click run_server.bat to start the server")
    print("  2. Open http://localhost:8000/docs in your browser")
    print("  3. Try uploading an embryo image!")
    print()
elif failed <= 3:
    print(f"{YELLOW}Setup is mostly complete with minor issues{RESET}")
    print()
    print("Please fix the failed checks above and run this script again.")
    print()
else:
    print(f"{RED}Setup needs attention{RESET}")
    print()
    print("Please address the failed checks above.")
    print("Refer to the setup guide for detailed instructions.")
    print()

print("For help, see:")
print("  - Setup Guide: G:/garba/deployment_new/README.md")
print()

# Save report
report_path = base_path / "setup_report.txt"
with open(report_path, 'w') as f:
    f.write("Setup Verification Report\n")
    f.write("=" * 60 + "\n")
    f.write(f"Passed: {passed}\n")
    f.write(f"Failed: {failed}\n")
    f.write(f"Warnings: {warnings}\n")
    
print(f"Report saved to: {report_path}")
print()

sys.exit(0 if failed == 0 else 1)