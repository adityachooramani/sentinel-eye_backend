#!/usr/bin/env python3
"""
EC2 Process Job - Complete Working Version (Memory-Optimized)
Downloads Sentinel-2 bands from public AWS S3, calculates NDVI/NDBI,
detects deforestation and urban expansion, generates PNG + TIF outputs.

Optimized to run on t3.medium (4GB RAM) by downsampling bands to ~40m
resolution before processing (~2745x2745 pixels instead of 10980x10980).
"""

import os
import sys
import json
import time
import gc
import boto3
import rasterio
import numpy as np
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning, message='invalid value')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from decimal import Decimal
from botocore import UNSIGNED
from botocore.config import Config
from rasterio.enums import Resampling

sys.path.append(os.path.expanduser("~/.local/lib/python3.11/site-packages"))

# --- CONFIGURATION ---
REGION = 'us-west-2'
RESULTS_BUCKET = 'landuse-rondonia-data-dev'
JOBS_TABLE = 'landuse-rondonia-analysis-jobs-dev'

# Output goes to /tmp so the shell script can find it
OUTPUT_DIR = Path('/tmp/landuse-processing')

# Downsample factor: 4 means 10m→40m resolution (~2745x2745 px per tile)
# This keeps total memory under 2GB for the full pipeline
DOWNSAMPLE_FACTOR = 4

# Clients
s3_public = boto3.client('s3', region_name='us-west-2', config=Config(signature_version=UNSIGNED))
s3_private = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
jobs_table = dynamodb.Table(JOBS_TABLE)

# --- TILE CONFIGURATION ---
TILE_BBOXES = {
    "20MPS": {"min_lon": -62.0923, "min_lat": -8.1410, "max_lon": -61.1886, "max_lat": -7.2339},
    "20MQS": {"min_lon": -61.1848, "min_lat": -8.1380, "max_lon": -60.2835, "max_lat": -7.2294},
    "20MRS": {"min_lon": -60.2778, "min_lat": -8.1329, "max_lon": -59.3791, "max_lat": -7.2231},
    "21MTM": {"min_lon": -59.7222, "min_lat": -8.1329, "max_lon": -58.8114, "max_lat": -7.2339},
    "21MUM": {"min_lon": -58.8152, "min_lat": -8.1380, "max_lon": -57.9058, "max_lat": -7.2366},
    "20LPR": {"min_lon": -62.0901, "min_lat": -9.0454, "max_lon": -61.1848, "max_lat": -8.1380},
    "20LQR": {"min_lon": -61.1805, "min_lat": -9.0420, "max_lon": -60.2778, "max_lat": -8.1329},
    "20LRR": {"min_lon": -60.2713, "min_lat": -9.0364, "max_lon": -59.3714, "max_lat": -8.1258},
    "21LTL": {"min_lon": -59.7287, "min_lat": -9.0364, "max_lon": -58.8152, "max_lat": -8.1380},
    "21LUL": {"min_lon": -58.8195, "min_lat": -9.0420, "max_lon": -57.9077, "max_lat": -8.1410},
    "20LPQ": {"min_lon": -62.0877, "min_lat": -9.9498, "max_lon": -61.1805, "max_lat": -9.0421},
    "20LQQ": {"min_lon": -61.1757, "min_lat": -9.9461, "max_lon": -60.2713, "max_lat": -9.0364},
    "20LRQ": {"min_lon": -60.2641, "min_lat": -9.9399, "max_lon": -59.3629, "max_lat": -9.0285},
    "21LTK": {"min_lon": -59.7359, "min_lat": -9.9399, "max_lon": -58.8195, "max_lat": -9.0421},
    "20LPP": {"min_lon": -62.0851, "min_lat": -10.8541, "max_lon": -61.1757, "max_lat": -9.9461},
    "20LQP": {"min_lon": -61.1704, "min_lat": -10.8500, "max_lon": -60.2642, "max_lat": -9.9399},
    "20LRP": {"min_lon": -60.2563, "min_lat": -10.8433, "max_lon": -59.3533, "max_lat": -9.9312},
    "21LTJ": {"min_lon": -59.7437, "min_lat": -10.8433, "max_lon": -58.8243, "max_lat": -9.9461},
    "20LNN": {"min_lon": -63.0000, "min_lat": -11.7599, "max_lon": -62.0851, "max_lat": -10.8541},
    "20LPN": {"min_lon": -62.0822, "min_lat": -11.7584, "max_lon": -61.1705, "max_lat": -10.8501},
    "20LQN": {"min_lon": -61.1647, "min_lat": -11.7540, "max_lon": -60.2563, "max_lat": -10.8433},
    "20LRN": {"min_lon": -60.2477, "min_lat": -11.7466, "max_lon": -59.3428, "max_lat": -10.8338},
    "20LNM": {"min_lon": -63.0000, "min_lat": -12.6642, "max_lon": -62.0822, "max_lat": -11.7584},
    "20LPM": {"min_lon": -62.0791, "min_lat": -12.6626, "max_lon": -61.1647, "max_lat": -11.7540},
    "20LQM": {"min_lon": -61.1585, "min_lat": -12.6578, "max_lon": -60.2477, "max_lat": -11.7466},
    "20LRM": {"min_lon": -60.2383, "min_lat": -12.6499, "max_lon": -59.3314, "max_lat": -11.7363},
    "20LNL": {"min_lon": -63.0000, "min_lat": -13.5685, "max_lon": -62.0791, "max_lat": -12.6626},
    "20LPL": {"min_lon": -62.0757, "min_lat": -13.5667, "max_lon": -61.1585, "max_lat": -12.6578},
    "20LQL": {"min_lon": -61.1517, "min_lat": -13.5616, "max_lon": -60.2383, "max_lat": -12.6499},
    "20LRL": {"min_lon": -60.2282, "min_lat": -13.5531, "max_lon": -59.3189, "max_lat": -12.6387},
    "20LNK": {"min_lon": -63.0000, "min_lat": -14.4726, "max_lon": -62.0757, "max_lat": -13.5667},
    "20LPK": {"min_lon": -62.0721, "min_lat": -14.4708, "max_lon": -61.1517, "max_lat": -13.5616},
    "20LQK": {"min_lon": -61.1445, "min_lat": -14.4653, "max_lon": -60.2282, "max_lat": -13.5531},
    "20LRK": {"min_lon": -60.2174, "min_lat": -14.4562, "max_lon": -59.3055, "max_lat": -13.5411},
    "20LNJ": {"min_lon": -63.0000, "min_lat": -15.3768, "max_lon": -62.0721, "max_lat": -14.4708},
    "20LPJ": {"min_lon": -62.0682, "min_lat": -15.3748, "max_lon": -61.1445, "max_lat": -14.4653},
    "20LQJ": {"min_lon": -61.1367, "min_lat": -15.3690, "max_lon": -60.2174, "max_lat": -14.4562},
    "20LRJ": {"min_lon": -60.2057, "min_lat": -15.3593, "max_lon": -59.2910, "max_lat": -14.4434},
}


def find_sentinel2_scene(tile_id, year):
    """
    Find a Sentinel-2 scene on the public AWS sentinel-cogs bucket.
    Path: sentinel-s2-l2a-cogs/{UTM_ZONE}/{LAT_BAND}/{GRID_SQ}/{YEAR}/{MONTH}/...
    Tries dry season months first (less cloud cover in Rondônia).
    """
    utm_zone = tile_id[:2]
    lat_band = tile_id[2]
    grid_sq = tile_id[3:5]
    
    # Preferred months: dry season first (less clouds), then others
    preferred_months = [7, 8, 6, 9, 5, 10, 4, 3, 11, 2, 1, 12]
    
    for month in preferred_months:
        prefix = f"sentinel-s2-l2a-cogs/{utm_zone}/{lat_band}/{grid_sq}/{year}/{month}/"
        try:
            response = s3_public.list_objects_v2(
                Bucket='sentinel-cogs',
                Prefix=prefix,
                Delimiter='/',
                MaxKeys=5
            )
            
            if 'CommonPrefixes' in response and len(response['CommonPrefixes']) > 0:
                scene_prefix = response['CommonPrefixes'][0]['Prefix']
                print(f"  Found scene: {scene_prefix}")
                return scene_prefix
                
        except Exception as e:
            continue
    
    return None


def download_band(scene_prefix, band_name, local_path):
    """Download a specific band from Sentinel-2 COGs on AWS."""
    s3_key = f"{scene_prefix}{band_name}.tif"
    print(f"  Downloading {s3_key}...")
    
    try:
        s3_public.download_file('sentinel-cogs', s3_key, str(local_path))
        print(f"  ✅ Downloaded {band_name} ({os.path.getsize(local_path) / 1024 / 1024:.1f} MB)")
        return True
    except Exception as e:
        print(f"  ❌ Failed to download {band_name}: {e}")
        return False


def read_band_downsampled(band_path, target_shape=None):
    """
    Read a band at reduced resolution to fit in memory.
    Returns: (data_array, profile) where profile has updated dimensions/transform.
    
    If target_shape is provided, reads to that exact shape (for matching bands).
    Otherwise uses DOWNSAMPLE_FACTOR.
    """
    with rasterio.open(band_path) as src:
        if target_shape is not None:
            out_h, out_w = target_shape
        else:
            out_h = src.height // DOWNSAMPLE_FACTOR
            out_w = src.width // DOWNSAMPLE_FACTOR
        
        data = src.read(
            1,
            out_shape=(out_h, out_w),
            resampling=Resampling.bilinear
        ).astype(np.float32)
        
        # Build a profile that reflects the downsampled dimensions
        profile = src.profile.copy()
        profile.update(
            height=out_h,
            width=out_w,
            transform=src.transform * src.transform.scale(
                src.width / out_w,
                src.height / out_h
            ),
            count=1,
            dtype='float32'
        )
    
    return data, profile


class LandUseProcessor:
    def __init__(self, job_id):
        self.job_id = job_id
        self.work_dir = OUTPUT_DIR / job_id
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Load job from DynamoDB
        job_item = self._load_job()
        self.created_at = job_item.get('created_at')
        self.tile_id = str(job_item.get('tile_id', '20LPN')).strip().upper().replace(" ", "")
        self.start_year = int(job_item.get('start_year', 2021))
        self.end_year = int(job_item.get('end_year', 2024))
        
        print(f"Job: {self.job_id}")
        print(f"Tile: {self.tile_id}")
        print(f"Years: {self.start_year} → {self.end_year}")
        print(f"Downsample: {DOWNSAMPLE_FACTOR}x (10m → {10 * DOWNSAMPLE_FACTOR}m effective)")
    
    def _load_job(self):
        from boto3.dynamodb.conditions import Key
        response = jobs_table.query(
            KeyConditionExpression=Key('job_id').eq(self.job_id)
        )
        if not response['Items']:
            raise ValueError(f"Job {self.job_id} not found in DynamoDB")
        return response['Items'][0]
    
    def update_status(self, status, progress=None, error=None):
        update_expr = 'SET #status = :status, updated_at = :updated'
        expr_values = {':status': status, ':updated': int(time.time())}
        
        if progress is not None:
            update_expr += ', progress = :progress'
            expr_values[':progress'] = progress
        if error:
            update_expr += ', error_message = :error'
            expr_values[':error'] = error
        
        try:
            jobs_table.update_item(
                Key={'job_id': self.job_id, 'created_at': self.created_at},
                UpdateExpression=update_expr,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=expr_values
            )
        except Exception as e:
            print(f"Warning: Could not update DynamoDB: {e}")
        
        print(f"[{status}] {progress}%")
    
    def download_sentinel_bands(self, year):
        """Download B04, B08, B11 for a given year and tile."""
        print(f"\n--- Downloading bands for {self.tile_id} / {year} ---")
        
        scene_prefix = find_sentinel2_scene(self.tile_id, year)
        if not scene_prefix:
            raise RuntimeError(f"No Sentinel-2 scene found for tile {self.tile_id}, year {year}")
        
        bands = {}
        for band in ['B04', 'B08', 'B11']:
            local_path = self.work_dir / f"{year}_{band}.tif"
            if local_path.exists() and local_path.stat().st_size > 1000:
                print(f"  ♻️  Using cached {band} ({local_path.stat().st_size / 1024 / 1024:.1f} MB)")
                bands[band] = local_path
            elif download_band(scene_prefix, band, local_path):
                bands[band] = local_path
            else:
                raise RuntimeError(f"Failed to download {band} for {year}")
        
        return bands
    
    def calculate_ndvi(self, bands, year, target_shape=None):
        """
        NDVI = (B08 - B04) / (B08 + B04)
        Reads at downsampled resolution to avoid OOM.
        """
        print(f"  Calculating NDVI for {year}...")
        
        # Read B04 (Red) at reduced resolution
        red, profile = read_band_downsampled(bands['B04'], target_shape=target_shape)
        actual_shape = (red.shape[0], red.shape[1])
        
        # Read B08 (NIR) at the same shape
        nir, _ = read_band_downsampled(bands['B08'], target_shape=actual_shape)
        
        # Calculate NDVI
        denom = nir + red
        ndvi = np.where(denom > 0, (nir - red) / denom, 0).astype(np.float32)
        ndvi = np.clip(ndvi, -1, 1)
        
        # Free band memory immediately
        del red, nir, denom
        gc.collect()
        
        # Save TIF
        ndvi_path = self.work_dir / f"{year}_ndvi.tif"
        save_profile = profile.copy()
        save_profile.update(compress='lzw')
        with rasterio.open(ndvi_path, 'w', **save_profile) as dst:
            dst.write(ndvi, 1)
        
        print(f"  NDVI {year}: shape={ndvi.shape}, min={ndvi.min():.3f}, max={ndvi.max():.3f}, mean={ndvi.mean():.3f}")
        return ndvi, ndvi_path, profile
    
    def calculate_ndbi(self, bands, year, target_shape=None):
        """
        NDBI = (B11 - B08) / (B11 + B08)
        Reads at downsampled resolution to avoid OOM.
        B11 is 20m native so it gets resampled to match the target shape.
        """
        print(f"  Calculating NDBI for {year}...")
        
        # Read B08 (NIR) at reduced resolution
        nir, profile = read_band_downsampled(bands['B08'], target_shape=target_shape)
        actual_shape = (nir.shape[0], nir.shape[1])
        
        # Read B11 (SWIR) and resample to match NIR shape
        swir, _ = read_band_downsampled(bands['B11'], target_shape=actual_shape)
        
        # Calculate NDBI
        denom = swir + nir
        ndbi = np.where(denom > 0, (swir - nir) / denom, 0).astype(np.float32)
        ndbi = np.clip(ndbi, -1, 1)
        
        # Free band memory immediately
        del nir, swir, denom
        gc.collect()
        
        # Save TIF
        ndbi_path = self.work_dir / f"{year}_ndbi.tif"
        save_profile = profile.copy()
        save_profile.update(compress='lzw')
        with rasterio.open(ndbi_path, 'w', **save_profile) as dst:
            dst.write(ndbi, 1)
        
        print(f"  NDBI {year}: shape={ndbi.shape}, min={ndbi.min():.3f}, max={ndbi.max():.3f}, mean={ndbi.mean():.3f}")
        return ndbi, ndbi_path, profile
    
    def detect_deforestation(self, ndvi_start, ndvi_end, profile):
        """Detect areas where vegetation was lost."""
        print("\n--- Detecting Deforestation ---")
        ndvi_diff = ndvi_end - ndvi_start
        
        # Thresholds:
        #   - NDVI dropped by more than 0.2
        #   - Start NDVI was vegetated (> 0.5)
        #   - End NDVI is bare/low (< 0.3)
        defor_mask = (
            (ndvi_diff < -0.2) &
            (ndvi_start > 0.5) &
            (ndvi_end < 0.3)
        )
        
        # Calculate area using the downsampled pixel size
        pixel_area_km2 = abs(profile['transform'][0] * profile['transform'][4]) / 1_000_000
        total_area = float(np.sum(defor_mask) * pixel_area_km2)
        pct = float(np.sum(defor_mask) / defor_mask.size * 100)
        
        print(f"  Deforestation: {total_area:.2f} km² ({pct:.2f}% of tile)")
        
        # Save TIF
        defor_path = self.work_dir / 'deforestation.tif'
        p = profile.copy()
        p.update(count=1, dtype='uint8', compress='lzw')
        with rasterio.open(defor_path, 'w', **p) as dst:
            dst.write(defor_mask.astype(np.uint8), 1)
        
        return defor_mask, total_area, pct, defor_path
    
    def detect_urban(self, ndbi_start, ndbi_end, profile):
        """Detect areas where urbanization increased."""
        print("--- Detecting Urban Expansion ---")
        ndbi_diff = ndbi_end - ndbi_start
        
        # Thresholds:
        #   - NDBI increased by more than 0.15
        #   - End NDBI shows built-up area (> 0.1)
        urban_mask = (
            (ndbi_diff > 0.15) &
            (ndbi_end > 0.1)
        )
        
        pixel_area_km2 = abs(profile['transform'][0] * profile['transform'][4]) / 1_000_000
        total_area = float(np.sum(urban_mask) * pixel_area_km2)
        pct = float(np.sum(urban_mask) / urban_mask.size * 100)
        
        print(f"  Urban expansion: {total_area:.2f} km² ({pct:.2f}% of tile)")
        
        urban_path = self.work_dir / 'urban_expansion.tif'
        p = profile.copy()
        p.update(count=1, dtype='uint8', compress='lzw')
        with rasterio.open(urban_path, 'w', **p) as dst:
            dst.write(urban_mask.astype(np.uint8), 1)
        
        return urban_mask, total_area, pct, urban_path
    
    def create_combined_tif(self, defor_mask, urban_mask, profile):
        """RGB combined: Red=deforestation, Blue=urban."""
        h, w = defor_mask.shape
        rgb = np.zeros((3, h, w), dtype=np.uint8)
        rgb[0][defor_mask] = 255  # Red channel
        rgb[2][urban_mask] = 255  # Blue channel
        
        combined_path = self.work_dir / 'combined_changes.tif'
        p = profile.copy()
        p.update(count=3, dtype='uint8', compress='lzw')
        with rasterio.open(combined_path, 'w', **p) as dst:
            dst.write(rgb)
        
        del rgb
        gc.collect()
        return combined_path
    
    def generate_png(self, start_ndvi, end_ndvi, start_ndbi, end_ndbi,
                     defor_mask, urban_mask, defor_area, urban_area, defor_pct, urban_pct):
        """Generate the 6-panel analysis PNG."""
        print("\n--- Generating Analysis PNG ---")
        
        # Further downsample for PNG rendering if arrays are still large
        max_dim = 1000
        factor = max(1, start_ndvi.shape[0] // max_dim)
        s_ndvi = start_ndvi[::factor, ::factor]
        e_ndvi = end_ndvi[::factor, ::factor]
        s_ndbi = start_ndbi[::factor, ::factor]
        e_ndbi = end_ndbi[::factor, ::factor]
        d_mask = defor_mask[::factor, ::factor]
        u_mask = urban_mask[::factor, ::factor]
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(
            f'Land Use Change Detection: {self.start_year} → {self.end_year}\n'
            f'Tile: {self.tile_id} | Resolution: {10 * DOWNSAMPLE_FACTOR}m',
            fontsize=16, fontweight='bold', y=0.98
        )
        
        # Row 1: NDVI start, NDVI end, Vegetation Loss
        im1 = axes[0, 0].imshow(s_ndvi, cmap='RdYlGn', vmin=0, vmax=1)
        axes[0, 0].set_title(f'NDVI {self.start_year}', fontsize=12)
        axes[0, 0].axis('off')
        plt.colorbar(im1, ax=axes[0, 0], fraction=0.046, pad=0.04)
        
        im2 = axes[0, 1].imshow(e_ndvi, cmap='RdYlGn', vmin=0, vmax=1)
        axes[0, 1].set_title(f'NDVI {self.end_year}', fontsize=12)
        axes[0, 1].axis('off')
        plt.colorbar(im2, ax=axes[0, 1], fraction=0.046, pad=0.04)
        
        # Vegetation loss panel: light background with red for deforested areas
        defor_vis = np.ones((*d_mask.shape, 3)) * np.array([0.95, 0.95, 0.92])
        defor_vis[d_mask] = [0.8, 0.0, 0.0]
        axes[0, 2].imshow(defor_vis)
        axes[0, 2].set_title(
            f'Vegetation Loss\n{defor_area:.1f} km² ({defor_pct:.2f}%)',
            fontsize=12, color='darkred'
        )
        axes[0, 2].axis('off')
        
        # Row 2: NDBI start, NDBI end, Combined
        im4 = axes[1, 0].imshow(s_ndbi, cmap='RdYlBu_r', vmin=-0.5, vmax=0.5)
        axes[1, 0].set_title(f'NDBI {self.start_year}', fontsize=12)
        axes[1, 0].axis('off')
        plt.colorbar(im4, ax=axes[1, 0], fraction=0.046, pad=0.04)
        
        im5 = axes[1, 1].imshow(e_ndbi, cmap='RdYlBu_r', vmin=-0.5, vmax=0.5)
        axes[1, 1].set_title(f'NDBI {self.end_year}', fontsize=12)
        axes[1, 1].axis('off')
        plt.colorbar(im5, ax=axes[1, 1], fraction=0.046, pad=0.04)
        
        # Combined changes: red=deforestation, blue=urban, black=no change
        h, w = d_mask.shape
        combined = np.zeros((h, w, 3))
        combined[d_mask] = [1, 0, 0]   # Red
        combined[u_mask] = [0, 0, 1]   # Blue
        axes[1, 2].imshow(combined)
        axes[1, 2].set_title(
            f'Combined Changes\nRed=Deforestation ({defor_area:.1f} km²)  Blue=Urban ({urban_area:.1f} km²)',
            fontsize=11
        )
        axes[1, 2].axis('off')
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        png_path = self.work_dir / 'analysis_result.png'
        fig.savefig(str(png_path), dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        # Free matplotlib memory
        del s_ndvi, e_ndvi, s_ndbi, e_ndbi, d_mask, u_mask, defor_vis, combined
        gc.collect()
        
        print(f"  PNG saved: {png_path} ({png_path.stat().st_size / 1024:.0f} KB)")
        return png_path
    
    def upload_results(self):
        """Upload all result files to S3."""
        print("\n--- Uploading Results to S3 ---")
        
        results_prefix = f"results/{self.job_id}"
        uploaded = {}
        
        files_to_upload = [
            ('deforestation.tif', 'deforestation'),
            ('urban_expansion.tif', 'urban_expansion'),
            ('combined_changes.tif', 'combined_map'),
            ('analysis_result.png', 'analysis_png'),
            (f'{self.start_year}_ndvi.tif', 'start_ndvi'),
            (f'{self.end_year}_ndvi.tif', 'end_ndvi'),
            (f'{self.start_year}_ndbi.tif', 'start_ndbi'),
            (f'{self.end_year}_ndbi.tif', 'end_ndbi'),
        ]
        
        for filename, key_name in files_to_upload:
            local_path = self.work_dir / filename
            if local_path.exists():
                s3_key = f"{results_prefix}/{filename}"
                size_mb = local_path.stat().st_size / 1024 / 1024
                print(f"  Uploading {filename} ({size_mb:.1f} MB)...")
                s3_private.upload_file(str(local_path), RESULTS_BUCKET, s3_key)
                uploaded[key_name] = f"s3://{RESULTS_BUCKET}/{s3_key}"
            else:
                print(f"  ⚠️ Skipping {filename} (not found)")
        
        # Save and upload summary JSON
        summary = {
            'job_id': self.job_id,
            'tile_id': self.tile_id,
            'start_year': self.start_year,
            'end_year': self.end_year,
            'resolution_m': 10 * DOWNSAMPLE_FACTOR,
            'completed_at': datetime.utcnow().isoformat(),
            'files': uploaded,
            'statistics': self._stats
        }
        
        summary_path = self.work_dir / 'summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        s3_private.upload_file(str(summary_path), RESULTS_BUCKET, f"{results_prefix}/summary.json")
        
        print(f"  ✅ Uploaded {len(uploaded)} files to s3://{RESULTS_BUCKET}/{results_prefix}/")
        return uploaded
    
    def run(self):
        """Main processing pipeline."""
        try:
            self.update_status('PROCESSING', progress=10)
            
            # === STEP 1: Download Sentinel-2 bands ===
            self.update_status('DOWNLOADING', progress=15)
            start_bands = self.download_sentinel_bands(self.start_year)
            
            self.update_status('DOWNLOADING', progress=30)
            end_bands = self.download_sentinel_bands(self.end_year)
            
            # === STEP 2: Calculate NDVI (downsampled) ===
            self.update_status('CALCULATING_NDVI', progress=45)
            start_ndvi, _, profile = self.calculate_ndvi(start_bands, self.start_year)
            target_shape = (start_ndvi.shape[0], start_ndvi.shape[1])
            end_ndvi, _, _ = self.calculate_ndvi(end_bands, self.end_year, target_shape=target_shape)
            
            # Ensure shapes match (safety check)
            if start_ndvi.shape != end_ndvi.shape:
                min_h = min(start_ndvi.shape[0], end_ndvi.shape[0])
                min_w = min(start_ndvi.shape[1], end_ndvi.shape[1])
                start_ndvi = start_ndvi[:min_h, :min_w]
                end_ndvi = end_ndvi[:min_h, :min_w]
                print(f"  ⚠️ Trimmed NDVI to matching shape: {start_ndvi.shape}")
            
            # === STEP 3: Calculate NDBI (downsampled, matched to NDVI shape) ===
            self.update_status('CALCULATING_NDBI', progress=60)
            start_ndbi, _, _ = self.calculate_ndbi(start_bands, self.start_year, target_shape=target_shape)
            end_ndbi, _, _ = self.calculate_ndbi(end_bands, self.end_year, target_shape=target_shape)
            
            if start_ndbi.shape != end_ndbi.shape:
                min_h = min(start_ndbi.shape[0], end_ndbi.shape[0])
                min_w = min(start_ndbi.shape[1], end_ndbi.shape[1])
                start_ndbi = start_ndbi[:min_h, :min_w]
                end_ndbi = end_ndbi[:min_h, :min_w]
                print(f"  ⚠️ Trimmed NDBI to matching shape: {start_ndbi.shape}")
            
            # Delete raw band files to free disk space (~900MB)
            print("\n  🧹 Cleaning up raw band files...")
            for f in self.work_dir.glob("*_B*.tif"):
                f.unlink()
                print(f"    Deleted {f.name}")
            gc.collect()
            
            # === STEP 4: Detect changes ===
            self.update_status('DETECTING_CHANGES', progress=70)
            defor_mask, defor_area, defor_pct, _ = self.detect_deforestation(
                start_ndvi, end_ndvi, profile
            )
            urban_mask, urban_area, urban_pct, _ = self.detect_urban(
                start_ndbi, end_ndbi, profile
            )
            # Store stats for summary.json
            self._stats = {
                'deforestation_km2': round(defor_area, 2),
                'deforestation_pct': round(defor_pct, 2),
                'urban_expansion_km2': round(urban_area, 2),
                'urban_expansion_pct': round(urban_pct, 2)
            }

            # === STEP 5: Create combined map ===
            self.update_status('CREATING_MAPS', progress=80)
            self.create_combined_tif(defor_mask, urban_mask, profile)
            
            # === STEP 6: Generate PNG ===
            self.update_status('GENERATING_PNG', progress=85)
            self.generate_png(
                start_ndvi, end_ndvi, start_ndbi, end_ndbi,
                defor_mask, urban_mask,
                defor_area, urban_area, defor_pct, urban_pct
            )
            
            # Free analysis arrays before upload
            del start_ndvi, end_ndvi, start_ndbi, end_ndbi, defor_mask, urban_mask
            gc.collect()
            
            # === STEP 7: Upload everything to S3 ===
            self.update_status('UPLOADING', progress=90)
            self.upload_results()
            
            # === DONE ===
            self.update_status('COMPLETED', progress=100)
            
            print(f"\n{'='*60}")
            print(f"✅ Job {self.job_id} COMPLETED SUCCESSFULLY")
            print(f"   Tile: {self.tile_id}")
            print(f"   Resolution: {10 * DOWNSAMPLE_FACTOR}m")
            print(f"   Deforestation: {defor_area:.2f} km² ({defor_pct:.2f}%)")
            print(f"   Urban growth:  {urban_area:.2f} km² ({urban_pct:.2f}%)")
            print(f"   Output dir:    {self.work_dir}")
            print(f"{'='*60}")
            
            # List output files for verification
            print("\nOutput files:")
            for f in sorted(self.work_dir.iterdir()):
                size_mb = f.stat().st_size / 1024 / 1024
                print(f"  {f.name} ({size_mb:.1f} MB)")
            
        except Exception as e:
            print(f"\n❌ PROCESSING FAILED: {e}")
            import traceback
            traceback.print_exc()
            self.update_status('FAILED', error=str(e))
            sys.exit(1)
	# === STEP 0: Clean ALL previous results from S3 ===
            print("\n🧹 Cleaning previous results from S3...")
            try:
                paginator = s3_private.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=RESULTS_BUCKET, Prefix='results/'):
                    if 'Contents' in page:
                        objects = [{'Key': obj['Key']} for obj in page['Contents']]
                        s3_private.delete_objects(
                            Bucket=RESULTS_BUCKET,
                            Delete={'Objects': objects}
                        )
                        print(f"  Deleted {len(objects)} old files from S3")
                print("  ✅ S3 cleanup done")
            except Exception as e:
                print(f"  ⚠️ S3 cleanup warning: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3.11 ec2_process_job.py <job_id>")
        sys.exit(1)
    
    job_id = sys.argv[1]
    print(f"\n{'='*60}")
    print(f"STARTING LAND USE PROCESSING")
    print(f"{'='*60}")
    
    processor = LandUseProcessor(job_id)
    processor.run()


if __name__ == '__main__':
    main()
