# 🛰️ Sentinel Eye

**On-demand satellite analysis for land-use change detection.**

Draw a region anywhere on Earth, and Sentinel Eye fetches real Sentinel-2 imagery, calculates vegetation and built-up indices, and produces downloadable GeoTIFF change maps showing exactly where deforestation and urban expansion have occurred between two years.

Built for the **Hyperspace Innovation Hackathon**. The infrastructure has since been torn down, but the full codebase and architecture are preserved here as a portfolio artifact.

---

## What It Does

A user draws a rectangle on the map. The system:

1. Fetches Sentinel-2 satellite imagery for that region from SentinelHub (for both a start year and an end year)
2. Saves the raw bands as GeoTIFFs in S3
3. Spins up an EC2 instance to calculate NDVI and NDBI indices from the raw bands
4. Compares the two time periods to detect deforestation and urban growth
5. Writes 7 result GeoTIFFs back to S3
6. Updates job status in DynamoDB throughout, so the frontend can poll for progress
7. Shuts the EC2 instance down automatically when done
8. Lets the user download any result file via a presigned S3 URL

The whole pipeline runs without any persistent compute cost — EC2 only exists for the duration of a job.

---

## Architecture

```
User draws region on map
        |
        v
React frontend  (InteractiveMap.jsx)
        |
        v  POST /api/analyze-region
API Gateway
        |
        v
Lambda: sentinel-fetcher  (lambda_sentinel_fetcher.py)
   - Creates a job record in DynamoDB
   - Authenticates with SentinelHub using credentials from Secrets Manager
   - Fetches Sentinel-2 bands (B02, B03, B04, B08, B11) for start year
   - Fetches Sentinel-2 bands for end year
   - Saves raw GeoTIFFs to S3
   - Launches an EC2 t3.medium with a startup script
        |
        v
EC2 instance  (ec2_dynamic_processor.py)
   - Downloads raw GeoTIFFs from S3
   - Calculates NDVI = (B08 - B04) / (B08 + B04) for both years
   - Calculates NDBI = (B11 - B08) / (B11 + B08) for both years
   - Applies thresholds to detect deforestation and urban expansion
   - Writes 7 result .tif files to S3
   - Updates job status to COMPLETED in DynamoDB
   - Shuts down automatically
        |
        v
Frontend polls /api/status/{job_id} every 5 seconds
        |
        v  POST /api/generate-download
Lambda: download-generator  (lambda_download_generator.py)
   - Returns a presigned S3 URL (valid for 1 hour)
        |
        v
User downloads .tif files
```

---

## Repository Structure

```
sentinel-eye_backend/
│
├── lambda_sentinel_fetcher.py      # Lambda 1: fetches Sentinel-2 imagery and launches EC2
├── lambda_download_generator.py    # Lambda 2: generates presigned S3 download URLs
├── ec2_dynamic_processor.py        # Runs on EC2: calculates indices, detects change
├── InteractiveMap.jsx              # React frontend component (reference client)
│
├── deploy_on_demand_processing.sh  # Automated deployment script
│
├── README_ON_DEMAND_PROCESSING.md  # Original implementation notes
├── DEPLOYMENT_GUIDE_ON_DEMAND_PROCESSING.md
├── QUICK_START.md
└── WORKFLOW_DIAGRAM.md
```

---

## How the Analysis Works

### Spectral Indices

Two indices are derived from raw Sentinel-2 bands.

**NDVI (Normalized Difference Vegetation Index)**

Measures vegetation health and density.

```
NDVI = (B08 - B04) / (B08 + B04)
     = (NIR  - Red) / (NIR  + Red)
```

| Value | Meaning |
|-------|---------|
| > 0.5 | Dense vegetation / forest |
| 0.2 to 0.5 | Sparse vegetation |
| < 0.2 | Bare soil, water, or built-up |

**NDBI (Normalized Difference Built-up Index)**

Measures how built-up an area is.

```
NDBI = (B11 - B08) / (B11 + B08)
     = (SWIR - NIR) / (SWIR + NIR)
```

| Value | Meaning |
|-------|---------|
| > 0.1 | Urban / built-up area |
| -0.1 to 0.1 | Bare soil |
| < -0.1 | Vegetation or water |

### Change Detection

After computing NDVI and NDBI for both years, the processor applies pixel-level thresholds.

**Deforestation** is flagged when a pixel satisfies all three conditions:

```python
deforestation = (
    (NDVI_end - NDVI_start < -0.2)  # NDVI dropped by more than 0.2
    & (NDVI_start > 0.5)             # Was forest at the start
    & (NDVI_end   < 0.3)             # Is no longer vegetation at the end
)
```

**Urban expansion** is flagged when:

```python
urban_expansion = (
    (NDBI_end - NDBI_start > 0.15)  # NDBI rose by more than 0.15
    & (NDBI_end > 0.1)              # Is now classified as built-up
)
```

### Output Files

Every completed job produces 7 GeoTIFFs in S3:

| File | Type | Description |
|------|------|-------------|
| `deforestation.tif` | Binary uint8 | 1 = deforested pixel, 0 = no change |
| `urban_expansion.tif` | Binary uint8 | 1 = new urban pixel, 0 = no change |
| `combined_changes.tif` | RGB uint8 | Red = deforestation, Blue = urban, Green = unchanged |
| `start_ndvi.tif` | Float32 | NDVI for the start year |
| `end_ndvi.tif` | Float32 | NDVI for the end year |
| `start_ndbi.tif` | Float32 | NDBI for the start year |
| `end_ndbi.tif` | Float32 | NDBI for the end year |

All files are GIS-ready and can be opened in QGIS, ArcGIS, or with Python (rasterio).

---

## API Reference

Both endpoints are exposed through API Gateway and backed by Lambda.

### POST /api/analyze-region

Submits an analysis job. Returns a `job_id` immediately while processing happens asynchronously.

**Request body:**

```json
{
  "bbox": {
    "min_lon": -63.5,
    "min_lat": -10.5,
    "max_lon": -63.0,
    "max_lat": -10.0
  },
  "start_year": 2021,
  "end_year": 2024,
  "change_types": ["deforestation", "urban"]
}
```

**Response:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PROCESSING",
  "message": "Sentinel-2 data fetched successfully. Processing started.",
  "ec2_instance_id": "i-0abcd1234efgh5678",
  "estimated_time": "5-10 minutes"
}
```

### POST /api/generate-download

Generates a presigned S3 URL for a result file. URLs expire after 1 hour.

**Request body:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_type": "deforestation",
  "s3_key": "results/550e8400-e29b-41d4-a716-446655440000/deforestation.tif"
}
```

**Response:**

```json
{
  "download_url": "https://s3.amazonaws.com/...",
  "expires_in": 3600,
  "file_type": "deforestation",
  "filename": "deforestation.tif"
}
```

### GET /api/status/{job_id}

Polled by the frontend every 5 seconds to track job progress. (Implemented in the frontend's `startPolling` function — a dedicated Lambda or DynamoDB read-through endpoint is needed for this in production.)

---

## Tech Stack

**Backend**

| Component | Technology |
|-----------|-----------|
| Runtime | Python 3.11 |
| Compute | AWS Lambda + EC2 t3.medium (auto-launched, auto-shutdown) |
| Storage | Amazon S3 (raw imagery and results) |
| Job tracking | Amazon DynamoDB |
| Satellite data | SentinelHub API (Sentinel-2 L2A, 10m resolution) |
| Geospatial | rasterio, numpy, geopandas |
| AWS SDK | boto3 |
| Secrets | AWS Secrets Manager |
| Monitoring | Amazon CloudWatch |

**Frontend**

| Component | Technology |
|-----------|-----------|
| Framework | React |
| Map | react-leaflet + leaflet-draw |
| HTTP | axios |

---

## Deployment

### Prerequisites

- AWS account with CLI configured (`aws configure`)
- Node.js and npm
- A SentinelHub account (free tier gives 10,000 processing units per month — sign up at https://www.sentinel-hub.com/)

### Step 1: Store SentinelHub credentials

Never put credentials in code. Store them in Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name sentinelhub-credentials \
  --secret-string '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  }' \
  --region us-west-2
```

### Step 2: Deploy backend

Run the automated deployment script:

```bash
chmod +x deploy_on_demand_processing.sh
./deploy_on_demand_processing.sh
```

This script:
- Creates a Lambda layer with sentinelhub, rasterio, and numpy
- Deploys `landuse-sentinel-fetcher` and `landuse-download-generator` Lambda functions
- Uploads `ec2_dynamic_processor.py` to S3 so EC2 instances can download it at startup
- Configures API Gateway endpoints
- Attaches the necessary IAM inline policy to the Lambda execution role

### Step 3: Set up the frontend

```bash
cd dashboard
npm install leaflet react-leaflet react-leaflet-draw axios
cp ../InteractiveMap.jsx src/components/
echo "REACT_APP_API_URL=https://YOUR_API_ID.execute-api.us-west-2.amazonaws.com/dev" > .env
npm start
```

### Step 4: Test

```bash
curl -X POST https://YOUR_API_ID.execute-api.us-west-2.amazonaws.com/dev/api/analyze-region \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {"min_lon": -63.5, "min_lat": -10.5, "max_lon": -63.0, "max_lat": -10.0},
    "start_year": 2021,
    "end_year": 2024,
    "change_types": ["deforestation", "urban"]
  }'
```

You should get back a `job_id`. After 5-10 minutes, the result files will appear in S3.

---

## Monitoring a Job

**Check job status in DynamoDB:**

```bash
aws dynamodb scan \
  --table-name landuse-rondonia-analysis-jobs-dev \
  --filter-expression "job_id = :jid" \
  --expression-attribute-values '{":jid":{"S":"YOUR_JOB_ID"}}' \
  --region us-west-2
```

**Check result files in S3:**

```bash
aws s3 ls s3://landuse-rondonia-data-dev/results/YOUR_JOB_ID/ --recursive
```

**Stream Lambda logs:**

```bash
aws logs tail /aws/lambda/landuse-sentinel-fetcher --follow
```

---

## Cost Estimates

All costs are per analysis job.

| Component | Small region (~50 km²) | Large region (~500 km²) |
|-----------|----------------------|------------------------|
| SentinelHub API | $0.10 to $0.30 | $0.30 to $0.70 |
| Lambda execution | $0.01 | $0.01 |
| EC2 t3.medium (10-15 min) | $0.01 | $0.02 |
| S3 storage | $0.05/month | $0.10/month |
| **Total per job** | **~$0.20** | **~$0.50** |

To reduce costs: use Spot instances for EC2 (saves up to 70%), compress output TIFFs with LZW (already done), and delete old results after 30 days with an S3 lifecycle rule.

---

## Security Notes

These are documented honestly, as they stood when the project was archived. Some practices are good; others would need work before going to production.

### What is done well

- **SentinelHub credentials in Secrets Manager.** The `get_sentinelhub_config()` function calls `GetSecretValue` at runtime. No credentials are hardcoded anywhere in the codebase.
- **Scoped Secrets Manager permission.** The IAM policy grants `GetSecretValue` only on the specific ARN `arn:aws:secretsmanager:REGION:ACCOUNT:secret:sentinelhub-credentials-*`, not on all secrets.
- **Presigned URL expiry.** Download URLs expire after 1 hour. Files are never made publicly accessible.
- **EC2 auto-shutdown.** The EC2 startup script ends with `sudo shutdown -h now`, so instances never idle.

### What would need hardening for production

- **No API authentication.** Both endpoints are open. Anyone who discovers the URL can trigger analysis jobs (which incur SentinelHub and EC2 costs) or call the download endpoint.
- **IDOR vulnerability in the download endpoint.** `lambda_download_generator.py` accepts an arbitrary `s3_key` from the caller and signs it directly. A caller can request a presigned URL for any object in the bucket, not just their own job's results. The fix is to derive the key server-side from `job_id` and `file_type`, ignoring the caller-supplied `s3_key`.
- **CORS is wide open.** All responses include `Access-Control-Allow-Origin: *`. This should be locked to your specific frontend domain.
- **Broad EC2 and IAM permissions.** The Lambda policy allows `ec2:RunInstances` and `iam:PassRole` on `Resource: "*"`. These should be scoped to specific instance profiles, AMIs, and roles.
- **Hardcoded AMI ID.** `ami-0c55b159cbfafe1f0` is a region-specific Amazon Linux 2 AMI that may be outdated. Pull the latest from SSM Parameter Store at deploy time instead.
- **Shell injection risk.** The EC2 startup script in `launch_processing_instance()` interpolates `job_id`, `start_data`, `end_data`, and `change_types` directly into a bash heredoc via Python f-string. If any of those values come from untrusted input without validation, this is a code injection vector.
- **Input validation is missing.** Bounding box coordinates and year values are not validated before use, which could lead to unbounded SentinelHub and EC2 costs from malformed requests.
- **EC2 fetches its script from S3.** The processing script is downloaded at instance startup from `s3://landuse-rondonia-data-dev/scripts/`. If that bucket is not locked down tightly, a compromised write to that path would execute arbitrary code on the next EC2 launch.

---

## Roadmap

These are features that were planned but not built before the hackathon ended.

- Display result GeoTIFFs directly on the map using `georaster-layer-for-leaflet`
- Add a `GET /api/status/{job_id}` Lambda so the frontend does not need to query DynamoDB directly
- Email or SMS notification when a job finishes
- Cache results for repeated requests on the same region and time period
- Time series mode: track change across more than two years
- Additional indices: NDWI (water bodies), SAVI (soil-adjusted vegetation), EVI
- Batch processing for multiple regions in a single request
- Add API key authentication before any public deployment

---

## References

- SentinelHub documentation: https://docs.sentinel-hub.com/
- Sentinel-2 spectral bands: https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/resolutions/radiometric
- rasterio documentation: https://rasterio.readthedocs.io/
- NDVI explained: https://gisgeography.com/ndvi-normalized-difference-vegetation-index/

---

## License

MIT. Built for the Hyperspace Innovation Hackathon.
