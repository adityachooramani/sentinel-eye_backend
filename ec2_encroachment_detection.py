#!/usr/bin/env python3
"""
Encroachment Detection Script
Detects changes within protected area boundaries
"""

import os
import sys
import json
import boto3
import rasterio
import numpy as np
import geopandas as gpd
from pathlib import Path
from datetime import datetime
from rasterio.mask import mask
from shapely.geometry import mapping

# --- CONFIGURATION ---
REGION = 'us-west-2'  # <--- FIXED: Added Region
BUCKET_NAME = 'landuse-rondonia-data-dev'
CHANGES_TABLE = 'landuse-rondonia-detected-changes-dev'
WORK_DIR = '/tmp/landuse-processing'

# Initialize AWS clients with Region
s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)

changes_table = dynamodb.Table(CHANGES_TABLE)

class EncroachmentDetector:
    def __init__(self, job_id, boundaries_path):
        self.job_id = job_id
        self.work_dir = Path(WORK_DIR) / job_id
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Load protected area boundaries
        print(f"Loading boundaries from {boundaries_path}")
        try:
            self.boundaries = gpd.read_file(boundaries_path)
            print(f"  Loaded {len(self.boundaries)} protected areas")
        except Exception as e:
            print(f"Error loading boundaries: {e}")
            sys.exit(1)

    def download_from_s3(self, s3_key, local_path):
        """Download file from S3"""
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Downloading s3://{BUCKET_NAME}/{s3_key}")
        try:
            s3.download_file(BUCKET_NAME, s3_key, str(local_path))
            return local_path
        except Exception as e:
            print(f"Error downloading {s3_key}: {e}")
            return None

    def upload_to_s3(self, local_path, s3_key):
        """Upload file to S3"""
        print(f"Uploading to s3://{BUCKET_NAME}/{s3_key}")
        try:
            s3.upload_file(str(local_path), BUCKET_NAME, s3_key)
        except Exception as e:
            print(f"Error uploading {s3_key}: {e}")

    def detect_encroachment_in_area(self, protected_area, change_raster_path):
        """Detect changes within a protected area"""
        try:
            with rasterio.open(change_raster_path) as src:
                # Reproject boundary to raster CRS if needed
                if protected_area.crs != src.crs:
                    protected_area = protected_area.to_crs(src.crs)
                
                # Mask raster to protected area
                # We map the geometry to a format rasterio understands
                geoms = [mapping(protected_area.geometry.iloc[0])]
                
                # The crop=True cuts the raster down to the bounding box of the shape
                out_image, out_transform = mask(src, geoms, crop=True)
                
                # Count changed pixels (value == 1)
                # out_image is (bands, height, width), so we check band 0
                change_mask = out_image[0] == 1
                num_changed = np.sum(change_mask)
                
                if num_changed > 0:
                    # Calculate area
                    # Transform[0] is pixel width, Transform[4] is pixel height (usually negative)
                    pixel_area_km2 = abs(out_transform[0] * out_transform[4]) / 1_000_000
                    total_area = num_changed * pixel_area_km2
                    
                    return {
                        'changed_pixels': int(num_changed),
                        'area_km2': float(total_area),
                        'has_encroachment': True
                    }
                
                return None
                
        except Exception as e:
            print(f"  Warning: Could not process area: {str(e)}")
            return None

    def run(self, deforestation_raster_path, urban_raster_path):
        """Main encroachment detection pipeline"""
        print("\n=== ENCROACHMENT DETECTION ===")
        
        encroachment_results = []
        
        for idx, area in self.boundaries.iterrows():
            area_name = area.get('NAME', f'Area_{idx}')
            area_type = area.get('DESIG', 'Unknown')
            
            print(f"\nChecking area: {area_name} ({area_type})")
            
            # 1. Check deforestation
            if os.path.exists(deforestation_raster_path):
                defor_result = self.detect_encroachment_in_area(
                    self.boundaries.iloc[[idx]],
                    deforestation_raster_path
                )
                
                if defor_result and defor_result['has_encroachment']:
                    print(f"  ⚠️  Deforestation encroachment: {defor_result['area_km2']:.4f} km²")
                    self.save_encroachment_record(area, 'deforestation', defor_result['area_km2'], idx)
                    
                    # Add to summary list
                    encroachment_results.append({
                        'area_name': area_name,
                        'type': 'deforestation',
                        'area_km2': defor_result['area_km2']
                    })

            # 2. Check urban expansion
            if os.path.exists(urban_raster_path):
                urban_result = self.detect_encroachment_in_area(
                    self.boundaries.iloc[[idx]],
                    urban_raster_path
                )
                
                if urban_result and urban_result['has_encroachment']:
                    print(f"  ⚠️  Urban encroachment: {urban_result['area_km2']:.4f} km²")
                    self.save_encroachment_record(area, 'urban', urban_result['area_km2'], idx)
                    
                    encroachment_results.append({
                        'area_name': area_name,
                        'type': 'urban',
                        'area_km2': urban_result['area_km2']
                    })

        print(f"\n✅ Total encroachments detected: {len(encroachment_results)}")
        self.save_summary(encroachment_results)
        return encroachment_results

    def save_encroachment_record(self, area, subtype, area_km2, idx):
        """Save a single encroachment record to DynamoDB"""
        centroid = area.geometry.centroid
        area_name = area.get('NAME', f'Area_{idx}')
        area_type = area.get('DESIG', 'Unknown')
        
        encroachment_item = {
            'change_id': f"{self.job_id}_encroachment_{subtype}_{idx}",
            'detected_at': int(datetime.utcnow().timestamp()),
            'job_id': self.job_id,
            'type': 'encroachment',
            'subtype': subtype,
            'area_km2': str(area_km2), # Convert float to string for DynamoDB Decimal compatibility
            'protected_area_name': area_name,
            'protected_area_type': area_type,
            'coordinates': {
                'lat': str(centroid.y),
                'lon': str(centroid.x)
            },
            'severity': 'high',
            # 'geojson': mapping(area.geometry) # Often too large for DynamoDB, omitting for safety
        }
        
        try:
            changes_table.put_item(Item=encroachment_item)
        except Exception as e:
            print(f"Error saving to DynamoDB: {e}")

    def save_summary(self, results):
        """Save summary JSON to S3"""
        summary_path = self.work_dir / 'encroachment_summary.json'
        
        summary_data = {
            'job_id': self.job_id,
            'total_encroachments': len(results),
            'encroachments': results
        }
        
        with open(summary_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        self.upload_to_s3(
            summary_path,
            f"results/{self.job_id}/encroachment_summary.json"
        )


def main():
    if len(sys.argv) < 4:
        print("Usage: python ec2_encroachment_detection.py <job_id> <defor_raster> <urban_raster>")
        sys.exit(1)
    
    job_id = sys.argv[1]
    defor_raster = sys.argv[2]
    urban_raster = sys.argv[3]
    
    print(f"Job ID: {job_id}")
    print(f"Deforestation Raster: {defor_raster}")
    print(f"Urban Raster: {urban_raster}")
    
    # 1. Download boundaries
    boundaries_s3_key = 'boundaries/protected-areas.geojson'
    boundaries_local = f'/tmp/boundaries.geojson'
    
    # We download manually here to ensure we have the file before initializing the class
    print(f"Downloading boundaries from s3://{BUCKET_NAME}/{boundaries_s3_key}")
    try:
        s3.download_file(BUCKET_NAME, boundaries_s3_key, boundaries_local)
    except Exception as e:
        print(f"CRITICAL ERROR: Could not download boundaries: {e}")
        print("Ensure 'boundaries/protected-areas.geojson' exists in your S3 bucket.")
        sys.exit(1)

    # 2. Run Detector
    detector = EncroachmentDetector(job_id, boundaries_local)
    detector.run(defor_raster, urban_raster)


if __name__ == '__main__':
    main()
