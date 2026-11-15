FROM python:3.11-slim
WORKDIR /app

# libexpat1: needed by rasterio (reads Sentinel 2 images); not in the slim image
RUN apt-get update && apt-get install -y --no-install-recommends curl libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY fluxara/    ./fluxara/
COPY scripts/    ./scripts/
COPY satellite_data/facilities/ ./satellite_data/facilities/

ENV PYTHONPATH=/app
EXPOSE 8000
# Apply migrations, then serve.
CMD ["sh", "-c", "alembic upgrade head && gunicorn -w 2 -k uvicorn.workers.UvicornWorker fluxara.api.main:app --bind 0.0.0.0:8000"]
