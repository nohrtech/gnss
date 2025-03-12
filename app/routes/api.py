from flask import Blueprint, request, jsonify, current_app, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..processors.gnss_processor import GNSSProcessor
from ..models import Dataset, BaseStation, AnalysisResult, db
import os
from datetime import datetime
import logging
import traceback
import json

bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

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
    """Handle file upload with detailed logging."""
    logger.info("=== Starting File Upload ===")
    logger.info(f"Request Method: {request.method}")
    logger.info(f"Request Headers: {dict(request.headers)}")
    logger.info(f"Request Form Data: {dict(request.form)}")
    logger.info(f"Request Files: {list(request.files.keys())}")
    
    try:
        if 'file' not in request.files:
            logger.error("No file part in request")
            response = make_response(json.dumps({
                'success': False,
                'error': 'No file provided'
            }), 400)
            response.headers['Content-Type'] = 'application/json'
            return response

        file = request.files['file']
        logger.info(f"File received: {file.filename}, Content-Type: {file.content_type}")
        
        if file.filename == '':
            logger.error("Empty filename received")
            response = make_response(json.dumps({
                'success': False,
                'error': 'No file selected'
            }), 400)
            response.headers['Content-Type'] = 'application/json'
            return response

        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            response = make_response(json.dumps({
                'success': False,
                'error': 'Invalid file type. Supported formats: NMEA, RINEX, XYZ'
            }), 400)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Upload directory verified: {upload_dir}")

        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        logger.info(f"Saving file to: {file_path}")
        file.save(file_path)
        logger.info("File saved successfully")

        # Create dataset entry
        try:
            dataset = Dataset(
                name=filename,
                format_type=filename.rsplit('.', 1)[1].lower(),
                user_id=current_user.id,
                base_station_id=request.form.get('base_station_id'),
                processing_status='pending'
            )
            db.session.add(dataset)
            db.session.commit()
            logger.info(f"Dataset created with ID: {dataset.id}")

            response_data = {
                'success': True,
                'dataset_id': dataset.id,
                'filename': filename
            }
            logger.info(f"Sending response: {response_data}")
            
            response = make_response(json.dumps(response_data), 200)
            response.headers['Content-Type'] = 'application/json'
            return response

        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            logger.error(traceback.format_exc())
            try:
                os.remove(file_path)
                logger.info("Cleaned up uploaded file after database error")
            except:
                logger.warning("Failed to clean up uploaded file")
                
            response = make_response(json.dumps({
                'success': False,
                'error': 'Database error while creating dataset'
            }), 500)
            response.headers['Content-Type'] = 'application/json'
            return response

    except Exception as e:
        logger.error(f"Unexpected error in upload: {str(e)}")
        logger.error(traceback.format_exc())
        response = make_response(json.dumps({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

@bp.route('/process/<int:dataset_id>', methods=['POST'])
@login_required
def process_dataset(dataset_id):
    """Process uploaded dataset and return JSON response."""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        if dataset.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Process the file
        file_path = os.path.join(current_app.root_path, 'uploads', dataset.name)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Dataset file not found'}), 404

        # Get base station if specified
        base_coords = None
        if dataset.base_station_id:
            base = BaseStation.query.get(dataset.base_station_id)
            if base:
                base_coords = (base.location.latitude, base.location.longitude, base.altitude)

        # Initialize processor and process file
        processor = GNSSProcessor(base_station_coords=base_coords)
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
            dataset.processing_status = 'failed'
            db.session.commit()
            return jsonify({'error': f'Processing error: {str(e)}'}), 500

        # Save results
        duration = (datetime.now() - start_time).total_seconds()
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
            'success': True,
            'dataset_id': dataset.id,
            'results': analysis.to_dict()
        })

    except Exception as e:
        current_app.logger.error(f"Processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    """List available base stations."""
    try:
        stations = BaseStation.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': station.id,
            'name': station.name,
            'latitude': station.location.latitude,
            'longitude': station.location.longitude,
            'altitude': station.altitude,
            'description': station.description
        } for station in stations])
    except Exception as e:
        current_app.logger.error(f"Error fetching base stations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
