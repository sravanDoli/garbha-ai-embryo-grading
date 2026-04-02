# Embryo Fragmentation Analysis API

YOLOv8-powered embryo fragmentation quantification system.

## Quick Start

### 1. Create Database
```sql
-- In pgAdmin or psql
CREATE DATABASE embryo_db;
```

### 2. Install Dependencies
```bash
conda activate embryo_D
pip install -r requirements.txt
```

### 3. Copy Model File
Copy your `best.pt` file to `G:\garba\deployment_new\models\`

### 4. Initialize Database
```bash
python init_database.py
```

### 5. Start Server
```bash
python run_server.bat
```

Or manually:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Access API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Dashboard**: http://localhost:8000/dashboard

## Project Structure
```
G:\garba\deployment_new\
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── database.py          # Database connection
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── utils.py             # Utility functions
├── init_database.py     # Database initialization
├── check_setup.py       # Setup verification
├── run_server.bat       # Server startup script
├── requirements.txt     # Python dependencies
├── models/
│   └── best.pt         # YOLOv8 model weights
├── uploads/            # Uploaded images
├── reports/            # Generated reports
├── logs/               # Application logs
└── backups/            # Database backups
```

## API Endpoints

### Prediction
- `POST /predict` - Analyze embryo image
- `GET /embryo/{embryo_id}` - Get embryo record
- `GET /embryo/{embryo_id}/heatmap` - Get visualization

### Patient & Center
- `GET /patient/{patient_id}/embryos` - Get patient embryos
- `GET /center/{center_id}/embryos` - Get center embryos
- `GET /statistics/{center_id}` - Get center statistics

### General
- `GET /health` - Health check
- `GET /dashboard` - Dashboard data

## Troubleshooting

### Database Connection Error
```bash
# Check if PostgreSQL is running
# Verify database exists:
psql -U postgres -l

# Create database if missing:
psql -U postgres -c "CREATE DATABASE embryo_db;"
```

### Model Loading Error
- Ensure `best.pt` exists in `models/` folder
- Check path in `config.py`

### Import Errors
```bash
pip install -r requirements.txt
```

## Support

For issues, check:
1. `python check_setup.py`
2. Server logs in console
3. Database connection settings in `config.py`