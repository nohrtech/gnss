# GNSS Data Processing Application

A web-based application for processing and visualizing GNSS data from various formats including NMEA, RINEX, and XYZ.

## Features

- Support for multiple GNSS data formats:
  - NMEA
  - RINEX
  - XYZ
- Real-time data visualization using:
  - Leaflet.js for mapping
  - Chart.js for accuracy metrics
  - D3.js for advanced visualizations
- Position accuracy analysis
- Satellite tracking
- Base station support

## Technology Stack

- **Backend**:
  - Python/Flask
  - PostgreSQL with PostGIS
  - MongoDB for raw data storage
  - Key Python libraries:
    - pynmea2
    - GeoRinex
    - pyubx2
    - pyproj

- **Frontend**:
  - JavaScript
  - D3.js
  - Chart.js
  - Leaflet.js

- **Security**:
  - HTTPS support
  - User authentication

- **Deployment**:
  - Docker support

## Installation

### Using Docker (Recommended)

1. Install Docker and Docker Compose on your system
   - [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
   - [Docker Engine for Linux](https://docs.docker.com/engine/install/)

2. Clone the repository:
   ```bash
   git clone https://github.com/nohrtech/gnss.git
   cd gnss
   ```

3. Start the application using Docker Compose:
   ```bash
   docker-compose up -d
   ```

   This will:
   - Build and start the Flask application
   - Start PostgreSQL with PostGIS extension
   - Start MongoDB
   - Initialize all required databases and tables
   - Set up the necessary environment

4. Access the application at `http://localhost:5000`

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nohrtech/gnss.git
   cd gnss
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the databases:
   - PostgreSQL with PostGIS
   - MongoDB

4. Configure environment variables in `.env`:
   ```
   FLASK_APP=app
   FLASK_ENV=development
   DATABASE_URL=postgresql://localhost/gnss_data
   MONGO_URI=mongodb://localhost:27017/
   SECRET_KEY=your-secret-key
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the development server:
   ```bash
   flask run
   ```

## Development

- The application follows a modular structure
- Database migrations are handled through Flask-Migrate
- Frontend assets are organized in the `app/static` directory
- Templates are in the `app/templates` directory

### Docker Development Tips

- View logs: `docker-compose logs -f`
- Rebuild containers: `docker-compose up -d --build`
- Access PostgreSQL: `docker-compose exec db psql -U postgres -d gnss_data`
- Access MongoDB: `docker-compose exec mongodb mongosh`

## Database Schema

The application uses PostgreSQL with PostGIS for storing:
- User accounts
- Base station information
- Dataset metadata
- Analysis results

MongoDB is used for storing raw GNSS data and temporary processing results.

## License

This project is proprietary software. All rights reserved.
