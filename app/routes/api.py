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
    """Process an uploaded dataset."""
    logger.info(f"=== Starting Dataset Processing {dataset_id} ===")
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Security check
        if dataset.user_id != current_user.id:
            logger.warning(f"Unauthorized access attempt to dataset {dataset_id} by user {current_user.id}")
            response = make_response(json.dumps({
                'success': False,
                'error': 'Unauthorized access'
            }), 403)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Process the dataset
        processor = GNSSProcessor(dataset)
        result = processor.process()
        
        if result:
            logger.info(f"Dataset {dataset_id} processed successfully")
            response = make_response(json.dumps({
                'success': True,
                'message': 'Dataset processed successfully'
            }), 200)
        else:
            logger.error(f"Failed to process dataset {dataset_id}")
            response = make_response(json.dumps({
                'success': False,
                'error': 'Processing failed'
            }), 500)
            
        response.headers['Content-Type'] = 'application/json'
        return response

    except Exception as e:
        logger.error(f"Error processing dataset {dataset_id}: {str(e)}")
        logger.error(traceback.format_exc())
        response = make_response(json.dumps({
            'success': False,
            'error': f'Processing error: {str(e)}'
        }), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

@bp.route('/base-stations', methods=['GET'])
@login_required
def get_base_stations():
    """Get list of base stations."""
    logger.info("=== Fetching Base Stations ===")
    try:
        base_stations = BaseStation.query.all()
        stations_data = []
        
        for station in base_stations:
            stations_data.append({
                'id': station.id,
                'name': station.name,
                'latitude': station.latitude,
                'longitude': station.longitude
            })
            
        logger.info(f"Returning {len(stations_data)} base stations")
        response = make_response(json.dumps(stations_data), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    except Exception as e:
        logger.error(f"Error fetching base stations: {str(e)}")
        logger.error(traceback.format_exc())
        response = make_response(json.dumps({
            'success': False,
            'error': f'Error fetching base stations: {str(e)}'
        }), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
