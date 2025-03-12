from . import db
from flask_login import UserMixin
from datetime import datetime
from geoalchemy2 import Geometry

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    datasets = db.relationship('Dataset', backref='owner', lazy=True)

class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    format_type = db.Column(db.String(20), nullable=False)  # NMEA, RINEX, XYZ
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    processing_status = db.Column(db.String(20), default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    base_station_id = db.Column(db.Integer, db.ForeignKey('base_station.id'))
    analysis_results = db.relationship('AnalysisResult', backref='dataset', lazy=True)

class BaseStation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(Geometry('POINT'), nullable=False)
    altitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

class AnalysisResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    reference_mode = db.Column(db.String(20), nullable=False)  # 'fixed' or 'floating'
    
    # Horizontal accuracy metrics
    horizontal_rmse = db.Column(db.Float)
    horizontal_std = db.Column(db.Float)
    horizontal_mean = db.Column(db.Float)
    horizontal_max = db.Column(db.Float)
    horizontal_min = db.Column(db.Float)
    
    # Vertical accuracy metrics
    vertical_rmse = db.Column(db.Float)
    vertical_std = db.Column(db.Float)
    vertical_mean = db.Column(db.Float)
    vertical_max = db.Column(db.Float)
    vertical_min = db.Column(db.Float)
    
    # Reference position
    reference_latitude = db.Column(db.Float)
    reference_longitude = db.Column(db.Float)
    reference_altitude = db.Column(db.Float)
    
    # Additional metadata
    num_points = db.Column(db.Integer)
    processing_duration = db.Column(db.Float)  # in seconds
    
    # XYZ-specific quality metrics
    solution_quality = db.Column(db.JSON)  # Stores std_dev_x, std_dev_y, std_dev_z
    xyz_stats = db.Column(db.JSON)  # Stores additional XYZ statistics
    
    def to_dict(self):
        """Convert analysis results to dictionary format"""
        result = {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'analysis_date': self.analysis_date.isoformat(),
            'reference_mode': self.reference_mode,
            'horizontal': {
                'rmse': self.horizontal_rmse,
                'std': self.horizontal_std,
                'mean': self.horizontal_mean,
                'max': self.horizontal_max,
                'min': self.horizontal_min
            },
            'vertical': {
                'rmse': self.vertical_rmse,
                'std': self.vertical_std,
                'mean': self.vertical_mean,
                'max': self.vertical_max,
                'min': self.vertical_min
            },
            'reference_position': {
                'latitude': self.reference_latitude,
                'longitude': self.reference_longitude,
                'altitude': self.reference_altitude
            },
            'num_points': self.num_points,
            'processing_duration': self.processing_duration
        }
        
        # Add XYZ-specific data if available
        if self.solution_quality:
            result['solution_quality'] = self.solution_quality
        if self.xyz_stats:
            result['xyz_stats'] = self.xyz_stats
            
        return result
