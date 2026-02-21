FROM public.ecr.aws/lambda/python:3.11

# Install system-level GDAL and PROJ dependencies
# proj-devel is required for pyproj/geopandas to install correctly
RUN yum install -y gdal gdal-devel proj proj-devel gcc-c++

# Install Python libraries with specific version pins
# Pinning pyproj avoids the 'executable not found' build error
RUN pip install --no-cache-dir \
    "numpy<2.0" \
    "rasterio==1.3.10" \
    "pyproj==3.6.1" \
    geopandas \
    boto3 \
    shapely \
    matplotlib

# Copy your processing script
COPY lambda_worker.py ${LAMBDA_TASK_ROOT}

CMD ["lambda_worker.lambda_handler"]
