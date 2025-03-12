import pynmea2
import georinex as gr
import numpy as np
from pyproj import Transformer
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from .xyz_processor import XYZProcessor

class GNSSProcessor:
    def __init__(self, base_station_coords: Optional[Tuple[float, float, float]] = None):
        """
        Initialize GNSS processor with optional base station coordinates
        
        Args:
            base_station_coords: Optional tuple of (lat, lon, height) for fixed base station
        """
        self.base_station_coords = base_station_coords
        self.transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)
        self.xyz_processor = XYZProcessor()
        
    def process_nmea(self, nmea_data: str) -> Dict:
        """Process NMEA data and return parsed results"""
        try:
            parsed_data = []
            for line in nmea_data.split('\n'):
                try:
                    if line.startswith('$GNGGA') or line.startswith('$GPGGA'):
                        msg = pynmea2.parse(line)
                        if msg.gps_qual > 0:  # Only process if we have a GPS fix
                            parsed_data.append({
                                'timestamp': datetime.combine(msg.datestamp or datetime.now().date(), 
                                                           msg.timestamp),
                                'latitude': msg.latitude,
                                'longitude': msg.longitude,
                                'altitude': msg.altitude,
                                'hdop': msg.horizontal_dil,
                                'satellites': msg.num_sats,
                                'quality': msg.gps_qual
                            })
                except pynmea2.ParseError:
                    continue
                    
            return self._compute_accuracy_metrics(parsed_data)
        except Exception as e:
            raise ValueError(f"Error processing NMEA data: {str(e)}")

    def process_rinex(self, rinex_file: str) -> Dict:
        """Process RINEX observation file and return parsed results"""
        try:
            # Read RINEX file
            obs = gr.load(rinex_file)
            
            parsed_data = []
            for time, data in obs.items():
                if 'C1' in data and 'L1' in data:  # Basic check for required observables
                    position = self._compute_position_from_rinex(data)
                    if position:
                        parsed_data.append({
                            'timestamp': time,
                            'latitude': position[0],
                            'longitude': position[1],
                            'altitude': position[2],
                            'satellites': len(data)
                        })
            
            return self._compute_accuracy_metrics(parsed_data)
        except Exception as e:
            raise ValueError(f"Error processing RINEX data: {str(e)}")

    def process_xyz(self, xyz_file: str) -> Dict:
        """Process XYZ format file and return parsed results"""
        try:
            # Process XYZ file using dedicated processor
            xyz_data = self.xyz_processor.process_xyz_file(xyz_file)
            
            # Extract position data for accuracy metrics
            parsed_data = [{
                'timestamp': point['timestamp'],
                'latitude': point['latitude'],
                'longitude': point['longitude'],
                'altitude': point['altitude'],
                'satellites': point['num_satellites']
            } for point in xyz_data['data']]
            
            # Compute accuracy metrics
            accuracy_metrics = self._compute_accuracy_metrics(parsed_data)
            
            # Combine with XYZ-specific statistics
            return {
                **accuracy_metrics,
                'xyz_stats': xyz_data['statistics'],
                'solution_quality': {
                    'std_dev_x': xyz_data['statistics']['mean_accuracy']['x'],
                    'std_dev_y': xyz_data['statistics']['mean_accuracy']['y'],
                    'std_dev_z': xyz_data['statistics']['mean_accuracy']['z']
                }
            }
        except Exception as e:
            raise ValueError(f"Error processing XYZ data: {str(e)}")

    def _compute_position_from_rinex(self, data: Dict) -> Optional[Tuple[float, float, float]]:
        """Compute approximate position from RINEX observables"""
        # This is a placeholder for actual RINEX position computation
        # In a real implementation, this would use proper algorithms for position determination
        return None

    def _compute_accuracy_metrics(self, data: List[Dict]) -> Dict:
        """Compute accuracy metrics from parsed GNSS data"""
        if not data:
            return {'error': 'No valid data points found'}

        # Convert to numpy arrays for efficient computation
        positions = np.array([[d['latitude'], d['longitude'], d['altitude']] for d in data])
        
        # Compute reference position
        if self.base_station_coords:
            reference = np.array(self.base_station_coords)
        else:
            # Floating reference mode - use mean position
            reference = np.mean(positions, axis=0)

        # Convert to UTM for accurate distance calculations
        utm_coords = []
        for pos in positions:
            east, north = self.transformer.transform(pos[1], pos[0])
            utm_coords.append([east, north, pos[2]])
        utm_coords = np.array(utm_coords)

        ref_east, ref_north = self.transformer.transform(reference[1], reference[0])
        ref_utm = np.array([ref_east, ref_north, reference[2]])

        # Compute errors
        errors = utm_coords - ref_utm
        horizontal_errors = np.sqrt(errors[:, 0]**2 + errors[:, 1]**2)
        vertical_errors = np.abs(errors[:, 2])

        # Compute statistics
        results = {
            'horizontal': {
                'rmse': np.sqrt(np.mean(horizontal_errors**2)),
                'std': np.std(horizontal_errors),
                'mean': np.mean(horizontal_errors),
                'max': np.max(horizontal_errors),
                'min': np.min(horizontal_errors)
            },
            'vertical': {
                'rmse': np.sqrt(np.mean(vertical_errors**2)),
                'std': np.std(vertical_errors),
                'mean': np.mean(vertical_errors),
                'max': np.max(vertical_errors),
                'min': np.min(vertical_errors)
            },
            'num_points': len(data),
            'reference_mode': 'fixed' if self.base_station_coords else 'floating',
            'reference_position': {
                'latitude': reference[0],
                'longitude': reference[1],
                'altitude': reference[2]
            }
        }

        return results
