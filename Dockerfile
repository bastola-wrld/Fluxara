FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ curl git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_api.txt .
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements_api.txt

# Copy application
COPY fluxara/          ./fluxara/
COPY satellite_data/processed/  ./satellite_data/processed/
COPY satellite_data/facilities/ ./satellite_data/facilities/
COPY checkpoints/      ./checkpoints/

EXPOSE 8000
# Use gunicorn with uvicorn workers for production stability
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "fluxara.api.main:app", "--bind", "0.0.0.0:8000"]
