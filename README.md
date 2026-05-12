# Fluxara

> **Deep-learning based atmospheric inversion system for real-time methane emission attribution**

Fluxara is a high-performance system designed to attribute greenhouse gas (methane) emission rates to specific industrial facilities using satellite data (TROPOMI) and meteorological wind fields (ERA5). By replacing traditional, computationally expensive Lagrangian particle dispersion models (like STILT) with a high-speed U-Net / Fourier Neural Operator (FNO) inversion engine, Fluxara can perform source attribution and quantification in milliseconds instead of hours.

## 🚀 Key Features

- **Neural Inversion Engine**: Uses a physics-constrained U-Net architecture (`FluxaraInversionNet`) to rapidly map 3D wind fields and atmospheric states to ground footprints, ensuring mass conservation.
- **Bayesian Uncertainty**: Employs Monte Carlo dropout-based Bayesian Ensembles to provide defensible confidence scores and 1-sigma uncertainties for every emission prediction.
- **Automated Data Pipeline**: Integrates directly with the Copernicus Data Space (CDS) API to fetch and process daily Sentinel-5P TROPOMI and ERA5 NetCDF files.
- **Mass Balance Attribution**: Computes highly accurate emission rates (kg/hr) using Gaussian plume mass balance approximations conforming to IPCC Tier 2 standards.
- **Real-Time API & Dashboard**: Features an async FastAPI backend and a responsive React frontend dashboard to monitor facilities, visualize plumes, and manage alerts.

## 📂 Project Structure

- `fluxara/` — Core Python package
  - `api/` — FastAPI application, routes, and Pydantic schemas.
  - `models/` — PyTorch neural network, Bayesian ensemble, and physics-based attributor.
  - `data/` — Satellite data downloaders, loaders, and preprocessors.
  - `database/` — SQLAlchemy async ORM models, CRUD, and connection logic.
  - `training/` — Model training loops and dataset definitions.
- `client/` — React frontend application built with Vite, Recharts, and Leaflet.
- `scripts/` — Utilities for benchmarking, database initialization, and data generation.
- `tests/` — Comprehensive test suites for models, data pipelines, and production APIs.
- `satellite_data/` — Cached TROPOMI/ERA5 data and normalisation statistics.
- `checkpoints/` — Pre-trained model weights.

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (Local or Docker)
- CDS API Account (for downloading satellite data)

### 1. Backend Setup

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_api.txt

# Configure environment variables
cp .env.example .env
# Ensure your DATABASE_URL and FLUXARA_DEV_KEY are set correctly

# Configure Copernicus CDS API credentials
# Ensure ~/.cdsapirc is properly configured with your API key
```

### 2. Database Initialization

Fluxara uses an async SQLAlchemy setup. Initialize the database and seed it with Permian Basin facilities:

```bash
python scripts/init_db_async.py
```

### 3. Frontend Setup

```bash
cd client
npm install
```

## 🚦 Running the Application

### Start the API Server

```bash
uvicorn fluxara.api.main:app --reload --host 0.0.0.0 --port 8000
```
The API documentation will be available at `http://localhost:8000/docs`.

### Start the React Dashboard

In a new terminal:
```bash
cd client
npm run dev
```
The dashboard will be available at `http://localhost:3000` (or `5173` depending on Vite configuration).

### Docker Deployment

Alternatively, you can run the entire stack using Docker Compose:

```bash
docker compose up --build -d
```

## 🧪 Testing

Run the full, unified test suite covering the data pipeline, AI model, Bayesian ensemble, attribution physics, and API routes:

```bash
pytest tests/test_suite_full.py -v
```

## 📝 Configuration

- **Mock Mode**: If a pre-trained model checkpoint (`fluxara_best.pt`) isn't found in `checkpoints/`, the API will automatically fall back to mock mode.
- **PostGIS**: By default, spatial operations use basic lat/lon columns. You can enable PostGIS by setting `USE_POSTGIS=true` in your `.env`.

## 📜 License

Copyright © 2026 Fluxara Technologies Inc. All rights reserved.
