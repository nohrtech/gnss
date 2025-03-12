#!/bin/bash

# Update package list
apt-get update

# Install system dependencies
apt-get install -y \
    python3-pip \
    python3-dev \
    postgresql \
    postgresql-contrib \
    postgresql-server-dev-all \
    postgis \
    mongodb \
    apache2 \
    libapache2-mod-wsgi-py3

# Enable Apache modules
a2enmod wsgi
a2enmod ssl
a2enmod rewrite

# Start and enable services
systemctl start postgresql
systemctl enable postgresql
systemctl start mongodb
systemctl enable mongodb

# Install Python dependencies
pip3 install -r ../requirements.txt

# Create PostgreSQL database and enable PostGIS
sudo -u postgres psql -c "CREATE DATABASE gnss_data;"
sudo -u postgres psql -d gnss_data -c "CREATE EXTENSION postgis;"

# Create MongoDB database
mongosh --eval "use gnss_raw_data"
