#!/bin/bash
set -e

# Initialize PostGIS
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;
EOSQL

# Create tables for:
# - User accounts
# - Base station information
# - Dataset metadata
# - Analysis results
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- User accounts
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(64) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(128) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Base station information
    CREATE TABLE IF NOT EXISTS base_stations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(64) NOT NULL,
        description TEXT,
        location GEOMETRY(POINT, 4326) NOT NULL,
        elevation DOUBLE PRECISION,
        status VARCHAR(20) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Dataset metadata
    CREATE TABLE IF NOT EXISTS datasets (
        id SERIAL PRIMARY KEY,
        name VARCHAR(128) NOT NULL,
        file_type VARCHAR(20) NOT NULL,
        file_path VARCHAR(255) NOT NULL,
        uploaded_by INTEGER REFERENCES users(id),
        base_station_id INTEGER REFERENCES base_stations(id),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Analysis results
    CREATE TABLE IF NOT EXISTS analysis_results (
        id SERIAL PRIMARY KEY,
        dataset_id INTEGER REFERENCES datasets(id),
        horizontal_accuracy DOUBLE PRECISION,
        vertical_accuracy DOUBLE PRECISION,
        solution_quality JSONB,
        num_satellites INTEGER,
        processing_time DOUBLE PRECISION,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
EOSQL
