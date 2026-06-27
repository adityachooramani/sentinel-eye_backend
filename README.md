# 🛰️ Sentinel Eye

**Serverless AWS backend with least-privilege IAM, secrets-managed credentials, and event-driven job monitoring for on-demand satellite land-use analysis.**

Built for the **Hyperspace Innovation Hackathon.** Infrastructure has since been torn down. Full codebase and architecture are preserved here as a portfolio artifact.

---

## Table of Contents

- [What This Is](#what-this-is)
- [Architecture](#architecture)
- [Security Architecture](#security-architecture)
- [IAM Policy: Least Privilege in Practice](#iam-policy-least-privilege-in-practice)
- [Job Monitoring and Alerting](#job-monitoring-and-alerting)
- [API Surface](#api-surface)
- [How the Analysis Works](#how-the-analysis-works)
- [Repository Structure](#repository-structure)
- [Tech Stack](#tech-stack)
- [Deployment](#deployment)
- [Threat Model](#threat-model)
- [Security Assessment](#security-assessment)
- [What I Would Harden Next](#what-i-would-harden-next)

---

## What This Is

Sentinel Eye is a serverless geospatial backend that processes Sentinel-2 satellite imagery on demand. A user selects any region on a map, and the system fetches real satellite bands from SentinelHub, runs spectral index calculations on a short-lived EC2 instance, detects land-use changes between two years, and returns presigned download links for 7 GeoTIFF result files.

The backend is designed around the principle of no persistent compute. The EC2 instance exists only for the duration of a job, shuts itself down on completion, and all credentials are externalized to AWS Secrets Manager. The job lifecycle is tracked in DynamoDB, which serves as the event state machine driving the pipeline.

---

## Architecture

The pipeline is fully event-driven. API Gateway receives a request, Lambda writes a job record to DynamoDB and kicks off the compute chain, EC2 processes the data and updates state, and the frontend polls job status until completion.

```
                    ┌─────────────────────────────────────────────┐
                    │              CLIENT (React)                  │
                    │  InteractiveMap.jsx                         │
                    │  draws bbox  →  polls /api/status/{job_id}  │
                    └────────────────┬────────────────────────────┘
                                     │  POST /api/analyze-region
                                     ▼
                    ┌─────────────────────────────────────────────┐
                    │         API Gateway  (no auth — see         │
                    │         Threat Model for remediation)       │
                    └────────────────┬────────────────────────────┘
                                     │  AWS_PROXY integration
                                     ▼
                    ┌─────────────────────────────────────────────┐
                    │     Lambda: landuse-sentinel-fetcher         │
                    │                                             │
                    │  1. Writes job record to DynamoDB           │
                    │     status: FETCHING_DATA, progress: 0      │
                    │                                             │
                    │  2. Calls Secrets Manager                   │
                    │     GetSecretValue → SentinelHub OAuth      │
                    │                                             │
                    │  3. Fetches Sentinel-2 bands from           │
                    │     SentinelHub API (B02,B03,B04,B08,B11)  │
                    │     for start_year and end_year             │
                    │                                             │
                    │  4. Saves raw GeoTIFFs to S3               │
                    │     s3://bucket/sentinel2-raw/{job_id}/     │
                    │                                             │
                    │  5. Updates DynamoDB → PROCESSING           │
                    │                                             │
                    │  6. ec2.run_instances() with UserData       │
                    │     script referencing job_id               │
                    └────────────────┬────────────────────────────┘
                                     │  EC2 launches with IAM instance profile
                                     ▼
                    ┌─────────────────────────────────────────────┐
                    │   EC2 t3.medium: ec2_dynamic_processor.py   │
                    │                                             │
                    │  Downloads raw GeoTIFFs from S3             │
                    │  Calculates NDVI and NDBI for both years    │
                    │  Applies change-detection thresholds        │
                    │  Writes 7 result .tif files to S3           │
                    │     s3://bucket/results/{job_id}/           │
                    │  Updates DynamoDB → COMPLETED               │
                    │  sudo shutdown -h now                       │
                    └────────────────┬────────────────────────────┘
                                     │  DynamoDB state change
                                     ▼
                    ┌─────────────────────────────────────────────┐
                    │    Lambda: landuse-download-generator        │
                    │    (invoked on client request)              │
                    │                                             │
                    │  Validates job_id exists in DynamoDB        │
                    │  Generates presigned S3 URL (1 hr TTL)      │
                    │  Returns download link                      │
                    └─────────────────────────────────────────────┘
```

---

## Security Architecture

Security decisions are made at each layer of the stack. This section explains what was implemented and why.

### Credential Handling: Secrets Manager

SentinelHub OAuth credentials (client ID and client secret) are never present in code, environment variables, or the deployment script. They are stored as a JSON object in AWS Secrets Manager and retrieved at Lambda invocation time:

```python
def get_sentinelhub_config():
    secrets = boto3.client('secretsmanager')
    secret = secrets.get_secret_value(SecretId='sentinelhub-credentials')
    creds = json.loads(secret['SecretString'])
    config = SHConfig()
    config.sh_client_id = creds['client_id']
    config.sh_client_secret = creds['client_secret']
    return config
```

The Lambda execution role is granted `GetSecretValue` only on the specific secret ARN, not on all secrets in the account. This means a compromised Lambda function cannot enumerate or read any other secret.

### Identity-Based IAM: Per-Resource Scoping

The Lambda execution role uses inline identity-based policies that scope every permission to the minimum required resource. Three distinct permission boundaries are applied:

**Secrets Manager access** is locked to the exact secret name pattern:
```
arn:aws:secretsmanager:REGION:ACCOUNT:secret:sentinelhub-credentials-*
```

**EC2 launch permission** is granted only for `RunInstances` and `CreateTags`. The instance profile passed via `iam:PassRole` is scoped by resource ARN rather than `*`.

**S3 access** is scoped to the project bucket (`landuse-rondonia-data-dev`) and specific key prefixes (`sentinel2-raw/`, `scripts/`, `results/`).

DynamoDB access is scoped to the two project tables (`analysis-jobs-dev` and `detected-changes-dev`).

### Compute Isolation: Ephemeral EC2

No always-on compute exists. The EC2 instance is launched per job and terminates itself after writing results. The final line of the UserData startup script is:

```bash
sudo shutdown -h now
```

This limits the blast radius of any instance-level compromise to the duration of one job (typically 10 to 15 minutes). The instance runs under its own IAM instance profile (`landuse-ec2-processing-role`) that is separate from the Lambda execution role.

### Presigned URLs: Time-Limited Access

Result files are never made public. All downloads go through `lambda_download_generator`, which calls `generate_presigned_url` with a 1-hour expiry:

```python
download_url = s3_client.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': BUCKET_NAME,
        'Key': s3_key,
        'ResponseContentDisposition': f'attachment; filename="{get_filename(s3_key)}"'
    },
    ExpiresIn=3600
)
```

After expiry the link returns 403. Files remain private in S3 indefinitely.

---

## IAM Policy: Least Privilege in Practice

This is a sanitized version of the inline policy attached to `landuse-rondonia-lambda-role-dev`. It shows how each permission is scoped to the minimum required resource rather than using wildcard ARNs.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadSentinelHubSecret",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-west-2:ACCOUNT_ID:secret:sentinelhub-credentials-*",
      "Comment": "Scoped to this secret only. Lambda cannot enumerate or read any other secret."
    },
    {
      "Sid": "LaunchProcessingInstance",
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:CreateTags"
      ],
      "Resource": "*",
      "Comment": "RunInstances requires * on resource — partially mitigated by iam:PassRole scope below."
    },
    {
      "Sid": "PassInstanceProfileOnly",
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::ACCOUNT_ID:role/landuse-ec2-processing-role",
      "Comment": "Lambda can only pass this one named role. It cannot escalate to admin roles."
    },
    {
      "Sid": "ProjectBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::landuse-rondonia-data-dev/sentinel2-raw/*",
        "arn:aws:s3:::landuse-rondonia-data-dev/scripts/*",
        "arn:aws:s3:::landuse-rondonia-data-dev/results/*"
      ],
      "Comment": "Scoped to specific key prefixes. Lambda cannot read or overwrite unrelated paths."
    },
    {
      "Sid": "JobStateTracking",
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-west-2:ACCOUNT_ID:table/landuse-rondonia-analysis-jobs-dev",
        "arn:aws:dynamodb:us-west-2:ACCOUNT_ID:table/landuse-rondonia-detected-changes-dev"
      ],
      "Comment": "Table-level scope. No access to other DynamoDB tables in the account."
    }
  ]
}
```

The `ec2:RunInstances` action requires `Resource: *` by AWS design. This is partially compensated for by scoping `iam:PassRole` to the exact instance profile ARN, which prevents Lambda from launching an instance with an admin role.

---

## Job Monitoring and Alerting

### Job State Machine

Every job is tracked in DynamoDB with a `status` field that moves through these states:

```
FETCHING_DATA  →  DATA_FETCHED  →  PROCESSING
    →  DOWNLOADING  →  CALCULATING_NDVI  →  CALCULATING_NDBI
    →  DETECTING_DEFORESTATION  →  DETECTING_URBAN
    →  CREATING_MAPS  →  FINALIZING  →  COMPLETED
                                              (or FAILED)
```

The `ec2_dynamic_processor.py` calls `update_progress()` at each stage, writing `status`, `progress` (0 to 100), and `updated_at` to the DynamoDB record. The frontend polls `/api/status/{job_id}` every 5 seconds and updates the progress bar from these values.

### CloudWatch Alerting

All Lambda invocations and EC2 startup logs stream to CloudWatch. You can set metric alarms on:

- Lambda error rate on `landuse-sentinel-fetcher` (SentinelHub auth failures, EC2 launch failures)
- Job records in `FAILED` state older than 30 minutes (DynamoDB Streams + Lambda consumer)
- EC2 instance running time exceeding 30 minutes (unexpected stall before auto-shutdown)

Example CloudWatch alarm for stuck jobs (CLI):

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "sentinel-eye-stuck-job" \
  --alarm-description "EC2 processing instance running longer than 30 minutes" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 1800 \
  --threshold 0.1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=tag:AutoShutdown,Value=true \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-west-2:ACCOUNT_ID:sentinel-eye-alerts
```

### Sample DynamoDB Job Record

This is what a completed job looks like in the `analysis-jobs-dev` table:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": 1735900000,
  "updated_at": 1735900720,
  "completed_at": 1735900720,
  "status": "COMPLETED",
  "progress": 100,
  "bbox": {
    "min_lon": -63.5,
    "min_lat": -10.5,
    "max_lon": -63.0,
    "max_lat": -10.0
  },
  "start_year": 2021,
  "end_year": 2024,
  "change_types": ["deforestation", "urban"],
  "ec2_instance_id": "i-0abcd1234efgh5678"
}
```

A FAILED record includes an additional `error_message` attribute written by the processor's exception handler.

---

## API Surface

Two endpoints are exposed through API Gateway, both backed by Lambda via AWS_PROXY integration.

### POST /api/analyze-region

Submits an analysis job. Returns a `job_id` immediately. Processing is asynchronous.

```bash
curl -X POST https://YOUR_API_ID.execute-api.us-west-2.amazonaws.com/dev/api/analyze-region \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {
      "min_lon": -63.5,
      "min_lat": -10.5,
      "max_lon": -63.0,
      "max_lat": -10.0
    },
    "start_year": 2021,
    "end_year": 2024,
    "change_types": ["deforestation", "urban"]
  }'
```

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

Generates a presigned S3 URL for a specific result file. Links expire after 1 hour.

```bash
curl -X POST https://YOUR_API_ID.execute-api.us-west-2.amazonaws.com/dev/api/generate-download \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_type": "deforestation",
    "s3_key": "results/550e8400-e29b-41d4-a716-446655440000/deforestation.tif"
  }'
```

```json
{
  "download_url": "https://landuse-rondonia-data-dev.s3.amazonaws.com/results/550e8400.../deforestation.tif?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600...",
  "expires_in": 3600,
  "file_type": "deforestation",
  "filename": "deforestation.tif"
}
```

---

## How the Analysis Works

### Spectral Indices

The EC2 processor reads five raw Sentinel-2 bands from GeoTIFF (B02, B03, B04, B08, B11) and derives two indices.

**NDVI — Normalized Difference Vegetation Index**

Measures vegetation density and health.

```
NDVI = (B08 - B04) / (B08 + B04)
     = (NIR - Red) / (NIR + Red)
```

Values above 0.5 indicate dense forest. Values below 0.2 indicate bare soil, water, or built-up surface.

**NDBI — Normalized Difference Built-up Index**

Measures urbanisation and impervious surface.

```
NDBI = (B11 - B08) / (B11 + B08)
     = (SWIR - NIR) / (SWIR + NIR)
```

Values above 0.1 indicate urban or built-up area.

### Change Detection Logic

After computing both indices for both years, the processor applies pixel-level boolean masks:

```python
# Deforestation: pixel was forest, is no longer forest, NDVI dropped significantly
deforestation_mask = (
    (ndvi_end - ndvi_start < -0.2)
    & (ndvi_start > 0.5)
    & (ndvi_end   < 0.3)
)

# Urban expansion: pixel became built-up and NDBI rose significantly
urban_expansion_mask = (
    (ndbi_end - ndbi_start > 0.15)
    & (ndbi_end > 0.1)
)
```

### Output Files

| File | Raster type | Contents |
|------|-------------|----------|
| `deforestation.tif` | Binary uint8 | 1 = deforested pixel |
| `urban_expansion.tif` | Binary uint8 | 1 = new urban pixel |
| `combined_changes.tif` | RGB uint8 | Red = deforestation, Blue = urban |
| `start_ndvi.tif` | Float32 (-1 to 1) | NDVI for start year |
| `end_ndvi.tif` | Float32 (-1 to 1) | NDVI for end year |
| `start_ndbi.tif` | Float32 (-1 to 1) | NDBI for start year |
| `end_ndbi.tif` | Float32 (-1 to 1) | NDBI for end year |

All outputs are LZW-compressed GeoTIFFs in EPSG:4326 and can be opened in QGIS, ArcGIS, or Python (rasterio).

---

## Repository Structure

```
sentinel-eye_backend/
│
├── lambda_sentinel_fetcher.py        # Lambda: fetches Sentinel-2 imagery, launches EC2
├── lambda_download_generator.py      # Lambda: generates presigned S3 download URLs
├── ec2_dynamic_processor.py          # EC2: calculates NDVI/NDBI, detects change, shuts down
├── InteractiveMap.jsx                # React reference client (map selection + download UI)
│
├── deploy_on_demand_processing.sh    # Automated deployment (Lambda, IAM, API Gateway)
│
├── README_ON_DEMAND_PROCESSING.md
├── DEPLOYMENT_GUIDE_ON_DEMAND_PROCESSING.md
├── QUICK_START.md
└── WORKFLOW_DIAGRAM.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | AWS API Gateway (HTTP API, AWS_PROXY integration) |
| Compute (short jobs) | AWS Lambda, Python 3.11 |
| Compute (processing) | EC2 t3.medium, auto-launched, auto-shutdown |
| Storage | Amazon S3 (raw imagery + results) |
| State / job tracking | Amazon DynamoDB |
| Secrets | AWS Secrets Manager |
| Satellite data | SentinelHub API, Sentinel-2 L2A at 10m resolution |
| Geospatial | rasterio, numpy, geopandas |
| Monitoring | Amazon CloudWatch Logs + Metrics |
| Frontend | React, react-leaflet, leaflet-draw, axios |

---

## Deployment

### Prerequisites

- AWS CLI configured (`aws configure`)
- Node.js and npm
- SentinelHub account (free tier: 10,000 processing units per month at https://www.sentinel-hub.com)

### Step 1: Store credentials in Secrets Manager

```bash
aws secretsmanager create-secret \
  --name sentinelhub-credentials \
  --secret-string '{
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  }' \
  --region us-west-2
```

### Step 2: Run the deployment script

```bash
chmod +x deploy_on_demand_processing.sh
./deploy_on_demand_processing.sh
```

This creates the Lambda layer (sentinelhub, rasterio, numpy), deploys both Lambda functions, uploads the EC2 processor script to S3, configures API Gateway routes, and attaches the IAM inline policy to the Lambda execution role.

### Step 3: Set up the frontend

```bash
cd dashboard
npm install leaflet react-leaflet react-leaflet-draw axios
cp ../InteractiveMap.jsx src/components/
echo "REACT_APP_API_URL=https://YOUR_API_ID.execute-api.us-west-2.amazonaws.com/dev" > .env
npm start
```

---

## Threat Model

Documented as a self-assessment. The first two items are implemented. Items three through six are known gaps.

**1. Credential exfiltration**
SentinelHub OAuth credentials are stored in Secrets Manager and retrieved at runtime. They are absent from code, environment variables, CloudWatch logs, and the deployment script. Risk: low.

**2. Blast radius on compute compromise**
EC2 instances auto-terminate after each job. A compromised instance has a window of roughly 10 to 15 minutes and can only access the S3 paths and DynamoDB tables permitted by its instance profile. It cannot reach Lambda roles or the Secrets Manager secret. Risk: contained.

**3. Unauthenticated API**
Both API Gateway endpoints have `AuthorizationType: NONE`. Any caller who discovers the URL can submit analysis jobs (triggering SentinelHub and EC2 costs) or call the download endpoint. Remediation: add an API Gateway API key or Cognito authorizer.

**4. Insecure Direct Object Reference (IDOR) on downloads**
`lambda_download_generator.py` accepts an `s3_key` from the caller and signs it directly without verifying that the key belongs to the caller's job. A caller can request a presigned URL for any object in the bucket. Remediation: derive the S3 key server-side from `job_id` and `file_type` only. Ignore the caller-supplied `s3_key`.

**5. Shell injection in EC2 UserData**
`launch_processing_instance()` builds the EC2 startup script by interpolating `job_id`, `start_data`, `end_data`, and `change_types` into a Python f-string bash heredoc. If these values are not validated before the Lambda handler processes them, a malicious payload in the request body could inject arbitrary shell commands that run on EC2 startup. Remediation: validate and sanitize all inputs at the API boundary before they reach the UserData builder.

**6. EC2 startup script integrity**
The EC2 instance downloads `ec2_dynamic_processor.py` from S3 at startup and executes it. If the bucket's write permissions are misconfigured and an attacker can overwrite that path, they control what runs on the next EC2 instance. Remediation: lock the `scripts/` prefix to `PutObject` from the Lambda role only, and consider adding a checksum verification step in UserData before execution.

---

## Security Assessment

This is a self-conducted posture review against the AWS security framework, covering what Prowler or ScoutSuite would flag and what remediation looks like.

> Note: Prowler and ScoutSuite were not run against this specific account before teardown. This section applies their standard check categories manually to the code and IAM policy as written.

| Check | Finding | Severity | Remediation |
|-------|---------|----------|-------------|
| API Gateway authentication | Both routes use `NONE` auth | High | Add API key or Cognito authorizer |
| CORS policy | `Access-Control-Allow-Origin: *` on all responses | Medium | Lock to frontend domain |
| S3 bucket public access | Not configured in code (assumed off by default) | Review | Explicitly set `BlockPublicAccess: true` on the bucket |
| ec2:RunInstances resource scope | Policy uses `Resource: *` | Medium | Partially mitigated by scoped `iam:PassRole`; add `aws:RequestedRegion` condition key |
| IAM `iam:PassRole` scope | Scoped to named role ARN | Pass | No action needed |
| Secrets Manager access scope | Scoped to exact secret ARN pattern | Pass | No action needed |
| CloudTrail logging | Not configured in codebase | Medium | Enable CloudTrail in the deployment account for API and IAM audit trail |
| Input validation | No bbox or year range validation | Medium | Add schema validation at Lambda handler entry point |
| EC2 instance in VPC | Not configured; defaults to default VPC | Medium | Place EC2 in a private subnet with a NAT gateway |
| KMS encryption at rest | S3 and DynamoDB use default encryption | Low | Switch to customer-managed KMS keys for audit key usage |

---

## What I Would Harden Next

These are the concrete next steps in priority order, not a wishlist.

**Fix the IDOR first.** The download endpoint is the most immediately exploitable issue. Change `lambda_download_generator.py` to build the S3 key from `job_id` and `file_type` and discard the caller-supplied `s3_key`. This is a one-function change.

**Add API Gateway authentication.** An API key with a usage plan takes 30 minutes to add and stops anonymous cost-triggering. Cognito user pools are the right long-term answer if user accounts are ever added.

**Validate inputs at the Lambda boundary.** Add a schema check on `bbox` (lat/lon range) and `year` (valid integer, not too far back) before any downstream call. This prevents cost abuse from malformed requests and closes the shell injection vector.

**Enable CloudTrail.** All IAM role assumptions, S3 writes, and Secrets Manager reads should be logged for audit. This is a one-command account-level change.

**Scope S3 write to `scripts/` prefix.** The EC2 startup script fetch path should only be writable by the Lambda role. Add an explicit `Deny` on `s3:PutObject` to the `scripts/` prefix for all principals except `landuse-rondonia-lambda-role-dev`.

**Replace hardcoded AMI ID.** `ami-0c55b159cbfafe1f0` is region-specific and may be outdated. Pull the latest Amazon Linux 2 AMI at deploy time from SSM Parameter Store:
```bash
aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2 \
  --query Parameter.Value --output text
```

---

## References

- SentinelHub documentation: https://docs.sentinel-hub.com/
- Sentinel-2 spectral bands: https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/resolutions/radiometric
- AWS IAM least-privilege guidance: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- Prowler AWS security tool: https://github.com/prowler-cloud/prowler
- ScoutSuite multi-cloud auditing: https://github.com/nccgroup/ScoutSuite
- rasterio documentation: https://rasterio.readthedocs.io/

---

## License

MIT. Built for the Hyperspace Innovation Hackathon.
