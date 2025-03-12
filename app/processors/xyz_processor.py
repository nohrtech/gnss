import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from pyproj import Transformer

class XYZProcessor:
    """Processor for XYZ format GNSS data files."""
    
    def __init__(self):
        self.ecef_to_lla = Transformer.from_crs(
            {"proj": "geocent", "ellps": "WGS84", "datum": "WGS84"},
            {"proj": "latlong", "ellps": "WGS84", "datum": "WGS84"},
            always_xy=True
        )

    def parse_xyz_line(self, line: str) -> Dict:
        """Parse a single line of XYZ data.
        
        Args:
            line: Raw line from XYZ file
            
        Returns:
            Dict containing parsed values
        """
        parts = line.strip().split()
        if len(parts) != 15:
            raise ValueError(f"Invalid XYZ line format: {line}")
            
        timestamp = datetime.datetime.strptime(
            f"{parts[0]} {parts[1]}", 
            "%Y/%m/%d %H:%M:%S.%f"
        )
        
        x, y, z = map(float, parts[2:5])
        solution_type = int(parts[5])
        num_satellites = int(parts[6])
        std_dev = list(map(float, parts[7:10]))
        additional_params = list(map(float, parts[10:13]))
        age = float(parts[13])
        ratio = float(parts[14])
        
        # Convert ECEF to lat/lon/alt
        lon, lat, alt = self.ecef_to_lla.transform(x, y, z)
        
        return {
            "timestamp": timestamp,
            "x": x,
            "y": y,
            "z": z,
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
            "solution_type": solution_type,
            "num_satellites": num_satellites,
            "std_dev_x": std_dev[0],
            "std_dev_y": std_dev[1],
            "std_dev_z": std_dev[2],
            "age": age,
            "ratio": ratio
        }

    def process_xyz_file(self, file_path: str) -> Dict:
        """Process an XYZ format file.
        
        Args:
            file_path: Path to XYZ file
            
        Returns:
            Dict containing processed data and statistics
        """
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    parsed = self.parse_xyz_line(line)
                    data.append(parsed)
                except (ValueError, IndexError) as e:
                    print(f"Warning: Skipping invalid line: {e}")
                    continue
        
        df = pd.DataFrame(data)
        
        # Calculate statistics
        stats = {
            "start_time": df["timestamp"].min(),
            "end_time": df["timestamp"].max(),
            "duration": (df["timestamp"].max() - df["timestamp"].min()).total_seconds(),
            "num_points": len(df),
            "mean_satellites": df["num_satellites"].mean(),
            "mean_position": {
                "latitude": df["latitude"].mean(),
                "longitude": df["longitude"].mean(),
                "altitude": df["altitude"].mean()
            },
            "std_position": {
                "latitude": df["latitude"].std(),
                "longitude": df["longitude"].std(),
                "altitude": df["altitude"].std()
            },
            "mean_accuracy": {
                "x": df["std_dev_x"].mean(),
                "y": df["std_dev_y"].mean(),
                "z": df["std_dev_z"].mean()
            }
        }
        
        return {
            "data": data,
            "statistics": stats
        }
