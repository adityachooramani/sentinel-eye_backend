sudo yum update -y
sudo yum install python3.11 python3.11-pip gdal gdal-devel -y
sudo yum update -y
sudo yum install python3.11 python3.11-pip gdal gdal-devel -y
pip --version
python3
gdal-config --version
sudo yum install python3.11 python3.11-pip python3.11-devel gcc -y
python3.11 -m pip --version
python3.11 -m pip install --upgrade pip
pip3.11 install numpy==1.26.4
pip3.11 install boto3 rasterio geopandas pandas shapely
python3.11 -c "import rasterio; print('✅ GDAL/Rasterio is working')"
nano ec2_process_job.py
nano ec2_encroachment_detection.py
python3.11 ec2_process_job.py test-job-001
nano ec2_process_job.py
python3.11 ec2_process_job.py test-job-001
nano ec2_process_job.py
python3.11 ec2_process_job.py test-job-001
sudo dd if=/dev/zero of=/swapfile bs=128M count=32
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
free -h
python3.11 ec2_process_job.py test-job-001
nano ec2_process_job.py
python3.11 ec2_process_job.py test-job-001
python3.11 ec2_encroachment_detection.py     test-job-001     /tmp/landuse-processing/test-job-001/deforestation.tif     /tmp/landuse-processing/test-job-001/urban_expansion.tif
nano ec2_encroachment_detection.py
python3.11 ec2_encroachment_detection.py     test-job-001     /tmp/landuse-processing/test-job-001/deforestation.tif     /tmp/landuse-processing/test-job-001/urban_expansion.tif
nano ec2_process_job.py
python3.11 ec2_encroachment_detection.py     test-job-001     /tmp/landuse-processing/test-job-001/deforestation.tif     /tmp/landuse-processing/test-job-001/urban_expansion.tif
nano ec2_process_job.py
python3.11 ec2_encroachment_detection.py     test-job-001     /tmp/landuse-processing/test-job-001/deforestation.tif     /tmp/landuse-processing/test-job-001/urban_expansion.tif
nano ec2_encroachment_detection.py
nano ec2_process_job.py
python3.11 ec2_encroachment_detection.py     test-job-001     /tmp/landuse-processing/test-job-001/deforestation.tif     /tmp/landuse-processing/test-job-001/urban_expansion.tif
nano ec2_process_job.py
python3.11 ec2_encroachment_detection.py     test-job-001     /tmp/landuse-processing/test-job-001/deforestation.tif     /tmp/landuse-processing/test-job-001/urban_expansion.tif
python3.11 ec2_process_job.py test-job-001
nano create_boundaries.py
python3.11 create_boundaries.py
aws s3 cp protected-areas.geojson s3://landuse-rondonia-data-dev/boundaries/protected-areas.geojson
python3.11 ec2_encroachment_detection.py     test-job-001     /tmp/landuse-processing/test-job-001/deforestation.tif     /tmp/landuse-processing/test-job-001/urban_expansion.tif
nano run_demo_mode.sh
chmod +x run_demo_mode.sh
./run_demo_mode.sh
find . -name "*.geojson"
nano create_sample_boundaries.py
python create_sample_boundaries.py
python3 create_sample_boundaries.py
pip install geopandas
python3 create_sample_boundaries.py
python3.11 create_sample_boundaries.py
aws s3 cp protected-areas.geojson     s3://landuse-rondonia-data-dev/boundaries/protected-areas.geojson
./run_demo_mode.sh
sudo rm -rf /tmp/landuse-processing/*
nano ec2_process_job.py
./run_demo_mode.sh
nano ec2_process_job.py
./run_demo_mode.sh
nano ec2_process_job.py
sudo growpart /dev/nvme0n1 1
sudo xfs_growfs -d /
nano ec2_process_job.py
./run_demo_mode.sh
exit
./run_demo_mode.sh
sudo rm -rf /tmp/landuse-processing/
df -h
sudo du -sh /* 2>/ignore | sort -h
sudo du -sh /* 2>/dev/null | sort -h
sudo du -sh /home/ec2-user/* 2>/dev/null | sort -h
rm -rf /home/ec2-user/landuse-processing/*
df -h
nano ec2_process_job.py
ps aux | grep run_demo_mode.sh
pkill -f run_demo_mode.sh
ps aux | grep run_demo_mode.sh
pkill -f run_demo_mode.sh
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
df -h
nano ec2_process_job.py
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
nano ec2_process_job.py
vim ec2_process_job.py
nano ec2_process_job.py
cat filename.txt | xclip -selection clipboard   
sudo apt install xclip
sudo dnf install xclip
sudo amazon-linux-extras install epel -y
sudo yum install xclip -y
sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
sudo yum-config-manager --enable epel
aws secretsmanager create-secret     --name sentinelhub-credentials     --secret-string '{
        "client_id": "5eb00575-007c-4bbd-8599-74e2c8762d3f",
        "client_secret": "6hb6L2gt9aq1yqA1docB40D6eZUfzsbm"
    }'     --region us-west-2
nano
nano ec2_process_job.py
n
nano ec2_process_job.py
tail -f worker.log
tail -n 20 ~/worker.log
[200~pkill -f run_demo_mode.sh~
pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
rm -rf ~/landuse-processing/*
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
python3 ~/ec2_process_job.py 979d193f-bb31-4770-b254-a8f9d9f7c4be
pip install boto3 botocore rasterio numpy
python3.11 -c "import boto3; print('✅ Boto3 is here')"
python3.11 ~/ec2_process_job.py 979d193f-bb31-4770-b254-a8f9d9f7c4be
nano ~/run_demo_mode.sh
tail -f worker.log
nano ~/run_demo_mode.sh'
nano ~/run_demo_mode.sh
python3.11 -c "import sys; print('\n'.join(sys.path))"
python3.11 /home/ec2-user/ec2_process_job.py 979d193f-bb31-4770-b254-a8f9d9f7c4be
dmesg | grep -i "out of memory"
sudo dmesg | grep -i "out of memory"
free -h
nano ec2_process_job.py
python3.11 ~/ec2_process_job.py 979d193f-bb31-4770-b254-a8f9d9f7c4be
pip install matplotlib
python3.11 ~/ec2_process_job.py 979d193f-bb31-4770-b254-a8f9d9f7c4be
> ~/worker.log
nohup ./run_demo_mode.sh > worker.log 2>&1 &
pkill -f ec2_process_job.py
pkill -f run_demo_mode.sh
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
curl -o protected-areas.geojson https://pda-data-br.s3.amazonaws.com/shapefiles/ro_protected_areas.geojson
aws s3 cp protected-areas.geojson s3://landuse-rondonia-data-dev/boundaries/protected-areas.geojson
nano ec2_process_job.py
pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
pkill -f ec2_encroachment_detection.py

cat /tmp/boundaries.geojson | head -n 10
cat <<EOF > /tmp/boundaries.geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": { "name": "Pacaás Novos National Park", "type": "National Park" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-64.0, -11.0], [-62.0, -11.0], [-62.0, -10.0], [-64.0, -10.0], [-64.0, -11.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Jaru Biological Reserve", "type": "Biological Reserve" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-63.0, -10.0], [-61.0, -10.0], [-61.0, -9.0], [-63.0, -9.0], [-63.0, -10.0]]]
      }
    }
  ]
}
EOF

python3 -c "import json; json.load(open('/tmp/boundaries.geojson')); print('✅ Local file is now valid GeoJSON')"
aws s3 cp /tmp/boundaries.geojson s3://landuse-rondonia-data-dev/boundaries/protected-areas.geojson
aws dynamodb update-item     --table-name landuse-rondonia-analysis-jobs-dev     --key '{"job_id": {"S": "680b3759-a6d3-454a-9197-43967d6bac84"}, "created_at": {"N": "PASTE_TIMESTAMP_HERE"}}'     --update-expression "SET #s = :s"     --expression-attribute-names '{"#s": "status"}'     --expression-attribute-values '{":s": {"S": "FAILED"}}'
aws dynamodb update-item     --table-name landuse-rondonia-analysis-jobs-dev     --key '{"job_id": {"S": "680b3759-a6d3-454a-9197-43967d6bac84"}, "created_at": {"N": "1770464874"}}'     --update-expression "SET #s = :s"     --expression-attribute-names '{"#s": "status"}'     --expression-attribute-values '{":s": {"S": "FAILED"}}'
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
pkill -f ec2_process_job.py
pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
aws dynamodb update-item     --table-name landuse-rondonia-analysis-jobs-dev     --key '{"job_id": {"S": "790e893a-73ae-4a7c-a1ea-f7e5f69736e5"}, "created_at": {"N": "1770462386"}}'     --update-expression "SET #s = :s"     --expression-attribute-names '{"#s": "status"}'     --expression-attribute-values '{":s": {"S": "FAILED"}}'
cat <<EOF > /tmp/boundaries.geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": { "name": "Pacaás Novos National Park", "type": "National Park" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-64.0, -11.0], [-62.0, -11.0], [-62.0, -10.0], [-64.0, -10.0], [-64.0, -11.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Jaru Biological Reserve", "type": "Biological Reserve" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-63.0, -10.0], [-61.0, -10.0], [-61.0, -9.0], [-63.0, -9.0], [-63.0, -10.0]]]
      }
    }
  ]
}
EOF

rm -rf /tmp/landuse-processing/*
python3.11 -c "import geopandas as gpd; gdf = gpd.read_file('/tmp/boundaries.geojson'); print(gdf)"
aws s3 cp /tmp/boundaries.geojson s3://landuse-rondonia-data-dev/boundaries/protected-areas.geojson
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
aws dynamodb update-item     --table-name landuse-rondonia-analysis-jobs-dev     --key '{"job_id": {"S": "200579ba-d27a-47db-9f9d-744ca22f3767"}, "created_at": {"N": "1770462386"}}'     --update-expression "SET #s = :s"     --expression-attribute-names '{"#s": "status"}'     --expression-attribute-values '{":s": {"S": "COMPLETED"}}'
cat <<EOF > /tmp/boundaries.geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": { "name": "Pacaás Novos National Park", "type": "National Park" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-64.0, -11.0], [-62.0, -11.0], [-62.0, -10.0], [-64.0, -10.0], [-64.0, -11.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Jaru Biological Reserve", "type": "Biological Reserve" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-63.0, -10.0], [-61.0, -10.0], [-61.0, -9.0], [-63.0, -9.0], [-63.0, -10.0]]]
      }
    }
  ]
}
EOF

# Upload to S3 so your script downloads the GOOD one
aws s3 cp /tmp/boundaries.geojson s3://landuse-rondonia-data-dev/boundaries/protected-areas.geojson
nano ec2_process_job.py
cat <<EOF > /tmp/boundaries.geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": { "name": "Pacaás Novos National Park", "type": "National Park" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-64.0, -11.0], [-62.0, -11.0], [-62.0, -10.0], [-64.0, -10.0], [-64.0, -11.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Jaru Biological Reserve", "type": "Biological Reserve" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-63.0, -10.0], [-61.0, -10.0], [-61.0, -9.0], [-63.0, -9.0], [-63.0, -10.0]]]
      }
    }
  ]
}
EOF

pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
> ~/worker.log
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
cat << 'EOF' > /tmp/boundaries.geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": { "name": "Pacaás Novos National Park", "type": "National Park" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-64.0, -11.0], [-62.0, -11.0], [-62.0, -10.0], [-64.0, -10.0], [-64.0, -11.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Jaru Biological Reserve", "type": "Biological Reserve" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-63.0, -10.0], [-61.0, -10.0], [-61.0, -9.0], [-63.0, -9.0], [-63.0, -10.0]]]
      }
    }
  ]
}
EOF

# Upload the fixed file to S3
aws s3 cp /tmp/boundaries.geojson s3://landuse-rondonia-data-dev/boundaries/protected-areas.geojson
nano ec2_process_job.py
pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
pkill -f ec2_encroachment_detection.py
cat << 'EOF' > /tmp/boundaries.geojson
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": { "name": "Pacaás Novos National Park", "type": "National Park" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-64.0, -11.0], [-62.0, -11.0], [-62.0, -10.0], [-64.0, -10.0], [-64.0, -11.0]]]
      }
    },
    {
      "type": "Feature",
      "properties": { "name": "Jaru Biological Reserve", "type": "Biological Reserve" },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[-63.0, -10.0], [-61.0, -10.0], [-61.0, -9.0], [-63.0, -9.0], [-63.0, -10.0]]]
      }
    }
  ]
}
EOF

aws dynamodb update-item     --table-name landuse-rondonia-analysis-jobs-dev     --key '{"job_id": {"S": "11d436fa-5506-4563-8e56-b88d2b5abb5e"}, "created_at": {"N": "PASTE_TIMESTAMP_HERE"}}'     --update-expression "SET #s = :s"     --expression-attribute-names '{"#s": "status"}'     --expression-attribute-values '{":s": {"S": "COMPLETED"}}'
nano run_demo_mode.sh
pkill -f run_demo_mode.sh
nano ~/run_demo_mode.sh
aws dynamodb query --table-name landuse-rondonia-analysis-jobs-dev --key-condition-expression "job_id = :j" --expression-attribute-values '{":j": {"S": "11d436fa-5506-4563-8e56-b88d2b5abb5e"}}' --query "Items[0].created_at.N" --output text
nohup ./run_demo_mode.sh > worker.log 2>&1 &
pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
> ~/worker.log
rm -rf /tmp/landuse-processing/*
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
sudo yum install jq -y
nano run_demo_mode.sh
pkill -f run_demo_mode.sh
rm -rf /tmp/landuse-processing/*
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
aws s3 ls s3://landuse-rondonia-data-dev/results/YOUR_NEW_JOB_ID/
pkill -f run_demo_mode.sh
nano ~/run_demo_mode.sh
rm -rf /home/ec2-user/landuse-processing/*
nohup ./run_demo_mode.sh > worker.log 2>&1 &
tail -f worker.log
python3.11 /home/ec2-user/ec2_process_job.py 29cf0554-8fa4-4b20-80bc-2b6f37bc56d8
sudo yum install jq -y
pkill -f run_demo_mode.sh
nano ~/run_demo_mode.sh
chmod +x ~/run_demo_mode.sh
rm -rf /tmp/landuse-processing/*
nohup ~/run_demo_mode.sh > ~/worker.log 2>&1 &
tail -f ~/worker.log
cat ~/ec2_process_job.py
cat ~/ec2_encroachment_detection.py
ls -la /tmp/landuse-processing/ 2>/dev/null || echo "Directory doesn't exist"
find /tmp -name "*.tif" 2>/dev/null || echo "No .tif files found anywhere in /tmp"
python3.11 ec2_process_job.py "9e3f3204-46c4-498c-aaa7-c3e79b26b8dd" 2>&1
nano ec2_process_job.py
nano run_demo_mode.sh
pkill -f run_demo_mode.sh
chmod +x ~/run_demo_mode.sh
pip3.11 install matplotlib --user
rm -rf /tmp/landuse-processing/*
python3.11 ~/ec2_process_job.py "YOUR_JOB_ID" 2>&1
# Get the most recent job ID from DynamoDB
aws dynamodb scan     --table-name landuse-rondonia-analysis-jobs-dev     --region us-west-2     --query "Items[0].{job_id: job_id.S, status: status.S, tile_id: tile_id.S}"     --output json
# 1. First, let's see ALL jobs in the table
aws dynamodb scan     --table-name landuse-rondonia-analysis-jobs-dev     --region us-west-2     --query "Items[*].{job_id: job_id.S, status: status.S, tile_id: tile_id.S, created_at: created_at.N}"     --output table
[200~python3.11 ~/ec2_process_job.py "680b3759-a6d3-454a-9197-43967d6bac84" 2>&1~
python3.11 ~/ec2_process_job.py "680b3759-a6d3-454a-9197-43967d6bac84" 2>&1
nano ~/ec2_process_job.py
rm -rf /tmp/landuse-processing/*
python3.11 ~/ec2_process_job.py "680b3759-a6d3-454a-9197-43967d6bac84" 2>&1
# Generate a temporary download link (valid for 1 hour)
aws s3 presign s3://landuse-rondonia-data-dev/results/680b3759-a6d3-454a-9197-43967d6bac84/analysis_result.png --expires-in 3600 --region us-west-2
# Run this on YOUR LOCAL machine (not EC2)
aws s3 cp s3://landuse-rondonia-data-dev/results/680b3759-a6d3-454a-9197-43967d6bac84/ ./sentinel-results/ --recursive --region us-west-2
pkill -f run_demo_mode.sh
nano ~/run_demo_mode.sh
chmod +x ~/run_demo_mode.sh
nohup ~/run_demo_mode.sh > ~/worker.log 2>&1 &
tail -f ~/worker.log
pkill -f run_demo_mode.sh
nano ~/run_demo_mode.sh
chmod +x ~/run_demo_mode.sh
nohup ~/run_demo_mode.sh > ~/worker.log 2>&1 &
tail -f ~/worker.log
nano ~/ec2_process_job.py
tail -f ~/worker.log
nano ~/ec2_process_job.py
tail -f ~/worker.log
cd /tmp/landuse-processing/
ls
nano ~/ec2_process_job.py
tail -f ~/worker.log
pkill -f run_demo_mode.sh
pkill -f ec2_process_job.py
nohup ~/run_demo_mode.sh > ~/worker.log 2>&1 &
tail -f ~/worker.log
nano ~/ec2_process_job.py
tail -f ~/worker.log
exit() exit()
exit
nohup ~/run_demo_mode.sh > ~/worker.log 2>&1 &
tail -f ~/worker.log
clear
tail -f ~/worker.log
clear
tail -f ~/worker.log
cat > Dockerfile << 'EOF'
FROM public.ecr.aws/lambda/python:3.11
FROM public.ecr.aws/lambda/python:3.1
[200~RUN yum install -y gdal gdal-devel gcc-c++
clear
exit
EOF

cat > Dockerfile << 'EOF'

FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y gdal gdal-devel gcc-c++

[200~RUN pip install --no-cache-dir \
~RUN pip install --no-cache-dir \

clear
EOF

cat > Dockerfile << 'EOF'
FROM public.ecr.aws/lambda/python:3.11

# Install GDAL and geospatial libraries
RUN yum install -y gdal gdal-devel gcc-c++
RUN pip install --no-cache-dir \
    rasterio \
    geopandas \
    numpy \
    boto3 \
    shapely

# Copy your processing script
COPY lambda_worker.py ${LAMBDA_TASK_ROOT}

CMD ["lambda_worker.lambda_handler"]
EOF

aws ecr create-repository --repository-name landuse-worker --region us-west-2
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 993125449267.dkr.ecr.us-west-2.amazonaws.com
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 993125449267.dkr.ecr.us-west-2.amazonaws.com
docker build -t landuse-worker .
cat > lambda_worker.py << 'EOF'
import json
import boto3
import rasterio
import numpy as np
import os
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Worker function to process specific Sentinel-2 tiles.
    """
    # 1. Parse job info (triggered by EventBridge or Direct)
    # 2. Download tile data from S3
    # 3. Perform NDVI/NDBI analysis
    # 4. Generate the 6-panel PNG plot
    # 5. Upload results back to S3
    
    print("Lambda Worker started processing job...")
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete!')
    }
EOF

docker build -t landuse-worker .
FROM public.ecr.aws/lambda/python:3.11
tail -f ~/worker.log
cat Dockerfile
nano Dockerfile
docker build -t landuse-worker .
nano Dockerfile
docker build -t landuse-worker .
docker tag landuse-worker:latest 993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest
docker push 993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest
aws lambda create-function     --function-name landuse-worker     --package-type Image     --code ImageUri=993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest     --role arn:aws:iam::993125449267:role/landuse-rondonia-lambda-role-dev     --memory-size 3008     --timeout 900     --region us-west-2
aws lambda invoke     --function-name landuse-worker     --payload '{"job_id": "manual-test-001", "tile_id": "20MPS"}'     --region us-west-2     response.json
aws lambda create-function     --function-name landuse-worker     --package-type Image     --code ImageUri=993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest     --role arn:aws:iam::993125449267:role/landuse-rondonia-lambda-role-dev     --memory-size 3008     --timeout 900     --region us-west-2
aws lambda create-function     --function-name landuse-worker     --package-type Image     --code ImageUri=993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest     --role arn:aws:iam::993125449267:role/landuse-rondonia-lambda-role-dev     --memory-size 3008     --timeout 900     --region us-west-2
aws lambda create-function     --function-name landuse-worker     --package-type Image     --code ImageUri=993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest     --role arn:aws:iam::993125449267:role/landuse-rondonia-lambda-role-dev     --memory-size 3008     --timeout 900     --region us-west-2
aws lambda create-function     --function-name landuse-worker     --package-type Image     --code ImageUri=993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest     --role arn:aws:iam::993125449267:role/landuse-rondonia-lambda-role-dev     --memory-size 3008     --timeout 900     --region us-west-2
aws lambda update-function-code     --function-name landuse-worker     --image-uri 993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest     --region us-west-2
aws lambda update-function-code     --function-name landuse-worker     --image-uri 993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest     --region us-west-2
aws lambda update-function-code     --function-name landuse-worker     --image-uri 993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest     --region us-west-2
aws lambda invoke     --function-name landuse-worker     --payload '{"job_id": "test-001", "tile_id": "20MPS"}'     --region us-west-2     output.json
aws lambda update-function-code     --function-name landuse-worker     --image-uri 993125449267.dkr.ecr.us-west-2.amazonaws.com/landuse-worker:latest     --region us-west-2
aws lambda invoke     --function-name landuse-worker     --cli-binary-format raw-in-base64-out     --payload '{"job_id": "test-final", "tile_id": "20MPS"}'     --region us-west-2     output.json
