"""
Database Configuration
File: database.py
Location: G:\garba\deployment_new\database.py
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Build PostgreSQL connection string from settings
DATABASE_URL = settings.DATABASE_URL

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False  # Set to True for debugging SQL queries
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()

print("✅ Database configuration loaded")
print(f"📍 Connected to: {settings.DB_NAME} database on {settings.DB_HOST}:{settings.DB_PORT}")