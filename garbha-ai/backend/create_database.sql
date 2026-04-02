-- ============================================
-- Create Embryo_db Database
-- Location: G:\garba\deployment_new\create_database.sql
-- ============================================

"""To run this SQL:

Open pgAdmin
Right-click on "PostgreSQL" server → Query Tool
Paste the SQL code
Click Execute (F5)
"""
-- Run this in pgAdmin or psql as postgres user

-- Drop database if exists (CAREFUL - THIS DELETES ALL DATA!)
DROP DATABASE IF EXISTS embryo_db;

-- Create new database
CREATE DATABASE embryo_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_United States.1252'
    LC_CTYPE = 'English_United States.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE embryo_db TO postgres;

-- Add comment
COMMENT ON DATABASE embryo_db 
    IS 'Embryo Fragmentation Analysis System Database';

-- Verify creation
SELECT datname, datdba, encoding, datcollate, datctype 
FROM pg_database 
WHERE datname = 'embryo_db';