from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..processors.gnss_processor import GNSSProcessor
from ..models import Dataset, BaseStation, AnalysisResult, db
import os
from datetime import datetime

bp = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {'nmea', 'rnx', 'rinex', 'xyz'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.before_app_first_request
def setup_upload_directory():
    upload_dir = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        # Check if file was included
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Supported formats: NMEA, RINEX, XYZ'}), 400

        # Ensure upload directory exists
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Create dataset entry
        dataset = Dataset(
            name=filename,
            format_type=filename.rsplit('.', 1)[1].lower(),
            user_id=current_user.id,
            base_station_id=request.form.get('base_station_id'),
            processing_status='pending'
        )
        db.session.add(dataset)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'dataset_id': dataset.id,
            'filename': filename
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Failed to upload file. Please try again.'}), 500

@bp.route('/process/<int:dataset_id>', methods=['POST'])
@login_required
def process_dataset(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Check ownership
        if dataset.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Get base station coordinates if specified
        base_coords = None
        if dataset.base_station_id:
            base = BaseStation.query.get(dataset.base_station_id)
            if base:
                base_coords = (base.location.latitude, base.location.longitude, base.altitude)
        
        # Initialize processor
        processor = GNSSProcessor(base_station_coords=base_coords)
        
        # Process based on file type
        file_path = os.path.join(current_app.root_path, 'uploads', dataset.name)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Dataset file not found'}), 404
            
        start_time = datetime.now()
        
        try:
            if dataset.format_type in ['nmea']:
                with open(file_path, 'r') as f:
                    results = processor.process_nmea(f.read())
            elif dataset.format_type in ['rnx', 'rinex']:
                results = processor.process_rinex(file_path)
            elif dataset.format_type == 'xyz':
                results = processor.process_xyz(file_path)
            else:
                return jsonify({'error': 'Unsupported file format'}), 400
        except Exception as e:
            current_app.logger.error(f"Processing error: {str(e)}")
            dataset.processing_status = 'failed'
            db.session.commit()
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
            
        # Calculate processing duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Save analysis results
        try:
            analysis = AnalysisResult(
                dataset_id=dataset.id,
                reference_mode='fixed' if base_coords else 'floating',
                horizontal_rmse=results['horizontal']['rmse'],
                horizontal_std=results['horizontal']['std'],
                horizontal_mean=results['horizontal']['mean'],
                horizontal_max=results['horizontal']['max'],
                horizontal_min=results['horizontal']['min'],
                vertical_rmse=results['vertical']['rmse'],
                vertical_std=results['vertical']['std'],
                vertical_mean=results['vertical']['mean'],
                vertical_max=results['vertical']['max'],
                vertical_min=results['vertical']['min'],
                reference_latitude=results['reference_position']['latitude'],
                reference_longitude=results['reference_position']['longitude'],
                reference_altitude=results['reference_position']['altitude'],
                num_points=results['num_points'],
                processing_duration=duration,
                solution_quality=results.get('solution_quality'),
                xyz_stats=results.get('xyz_stats')
            )
            
            db.session.add(analysis)
            dataset.processing_status = 'completed'
            db.session.commit()
            
            return jsonify({
                'message': 'Processing completed successfully',
                'dataset_id': dataset.id,
                'results': analysis.to_dict()
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Error saving results: {str(e)}")
            dataset.processing_status = 'failed'
            db.session.commit()
            return jsonify({'error': 'Error saving analysis results'}), 500
        
    except Exception as e:
        current_app.logger.error(f"General processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/results/<int:dataset_id>', methods=['GET'])
@login_required
def get_results(dataset_id):
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Check ownership
        if dataset.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access'}), 403
            
        results = AnalysisResult.query.filter_by(dataset_id=dataset_id).all()
        return jsonify({
            'dataset': {
                'id': dataset.id,
                'name': dataset.name,
                'format_type': dataset.format_type,
                'upload_date': dataset.upload_date.isoformat(),
                'processing_status': dataset.processing_status
            },
            'results': [result.to_dict() for result in results]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching results: {str(e)}")
        return jsonify({'error': 'Error fetching results'}), 500

@bp.route('/base-stations', methods=['GET'])
@login_required
def list_base_stations():
    try:
        stations = BaseStation.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': station.id,
            'name': station.name,
            'latitude': station.location.latitude,
            'longitude': station.location.longitude,
            'altitude': station.altitude,
            'description': station.description
        } for station in stations]), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching base stations: {str(e)}")
        return jsonify({'error': 'Error fetching base stations'}), 500
