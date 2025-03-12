#!/bin/bash
# GNSS Data Processing Application Installation Script
# Platform: Linux/Unix

echo "Installing GNSS Data Processing Application..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "This script must be run as root"
    exit 1
fi

# Update package list
apt-get update

# Install system dependencies
apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    postgresql \
    postgresql-contrib \
    postgresql-server-dev-all \
    postgis \
    mongodb

# Create Python virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt

# Initialize PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE gnss_data;"
sudo -u postgres psql -d gnss_data -c "CREATE EXTENSION postgis;"

# Create MongoDB database
mongosh --eval "use gnss_raw_data"

echo "Installation completed!"
echo "Configuration:"
echo "- PostgreSQL:"
echo "  - Database: gnss_data"
echo "  - Username: postgres"
echo "  - Password: postgres"
echo "  - Port: 5432"
echo "- MongoDB:"
echo "  - URL: mongodb://localhost:27017/"
echo "  - Database: gnss_raw_data"
