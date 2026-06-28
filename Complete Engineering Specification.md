

# DOCUMENT 3 — FULL TECHNICAL SPECIFICATION DOCUMENT

## Fluxara: Complete Engineering Specification

**Prepared for:** Technical Co-founders, Engineering Hires, and Due Diligence Reviewers
**Version:** 0.9 — Pre-implementation Architecture Specification
**Date:** June 2026
**Status:** Architecture complete, implementation pending

---

## 1. SYSTEM OVERVIEW

Fluxara is a real-time satellite greenhouse gas attribution system. Its function is to ingest freely available TROPOMI satellite methane observations and ERA5 meteorological reanalysis data, apply a trained neural atmospheric inversion model, attribute emission rates in kg/hr to specific industrial facilities registered in the EPA GHGRP and EU E-PRTR facility databases, quantify attribution uncertainty using Bayesian Monte Carlo Dropout, and generate regulatory-grade MRV reports.

**Performance targets:**
- Inference time: ≤ 8 seconds per basin-scale scene (1,000 × 1,000 km domain)
- Attribution accuracy: 86% against STILT physics baseline on held-out validation set
- Mean Absolute Error: 14% versus EPA GHGRP reported emission values
- Speedup factor: 1,801× versus 4-hour STILT baseline

---

## 2. DATA SOURCES AND LICENSING

### 2.1 TROPOMI Sentinel-5P — Primary Observation Source

**Instrument:** TROPOspheric Monitoring Instrument (TROPOMI) aboard ESA Sentinel-5 Precursor satellite

**Product used:** OFFL L2__CH4___ (Offline Level 2 Methane Total Column), Collection 03, version 2.x

**Key variables ingested:**
- `methane_mixing_ratio_bias_corrected` — XCH4 column-averaged dry-air mole fraction (ppb), bias-corrected for surface albedo dependence. This is the primary signal variable.
- `methane_mixing_ratio_precision` — per-pixel single-sounding precision (ppb)
- `qa_value` — quality assurance flag (dimensionless, 0–1). Fluxara applies threshold: `qa_value > 0.5` for valid pixels
- `latitude`, `longitude` — pixel centre coordinates (degrees)
- `latitude_bounds`, `longitude_bounds` — four-corner pixel geometry (degrees), used for area-weighted regridding
- `solar_zenith_angle` — (degrees), used for daytime-only filtering
- `surface_albedo_SWIR` — (dimensionless), used for retrieval quality assessment

**Spatial resolution:** 5.5 × 7 km² (post-August 2019)

**Temporal cadence:** 14 daily orbits, near-global coverage with ~1-day repeat. OFFL products available 3–5 days after sensing. NRTI (Near Real-Time) products available within 3 hours but at lower quality.

Data are stored in individual files (granules) containing one orbit of information in NetCDF4 format, with complete files approximately 82 MB each.

**Access method:** Copernicus Data Space Ecosystem API (https://dataspace.copernicus.eu), free registration required. Mirror access via Microsoft Azure Blob Storage (sentinel5euwest.blob.core.windows.net/sentinel-5p) and AWS S3 (s3://meeo-s5p/OFFL/L2__CH4___/).

**Licensing:** Free and open access under Copernicus Open Licence. No charge, no attribution restriction for commercial use.

**Latency in Fluxara pipeline:** OFFL products ingested 5–7 days post-sensing. For operational use requiring shorter latency, NRTI products used with quality-flag filtering.

### 2.2 ERA5 Reanalysis — Meteorological Input

**Product:** ERA5 hourly data on single levels and pressure levels, produced by ECMWF

**Variables ingested (single-level):**
- `u10` — 10 m U-component of wind (m/s)
- `v10` — 10 m V-component of wind (m/s)
- `u100` — 100 m U-component of wind (m/s)
- `v100` — 100 m V-component of wind (m/s)
- `blh` — Boundary Layer Height (m)
- `sp` — Surface pressure (Pa)
- `t2m` — 2 m temperature (K)
- `tcwv` — Total column water vapour (kg/m²)

**Variables ingested (pressure levels at 850, 700, 500 hPa):**
- `u` — U-component of wind (m/s)
- `v` — V-component of wind (m/s)
- `z` — Geopotential height (m²/s²)

**Spatial resolution:** 0.25° × 0.25° (~31 km at equator), regridded to 0.05° × 0.05° for alignment with TROPOMI

**Temporal resolution:** Hourly. ERA5 matched to TROPOMI overpass time (nearest hour)

**Access method:** Copernicus Climate Data Store (CDS) API via Python `cdsapi` package (version ≥ 0.7.0). Authenticated access with free CDS account. Access requires a personal access token stored in `~/.cdsapirc` and agreement to dataset terms of use.

**Licensing:** Copernicus Licence to use Copernicus Products. Free for commercial use with attribution.

**Latency:** ERA5 available with 5-day lag from real time.

### 2.3 EPA Greenhouse Gas Reporting Program (GHGRP) — US Facility Registry

**Purpose:** Ground truth facility locations, identifiers, and reported annual methane emission rates for training target labels and attribution matching.

For reporting year 2023, over 8,000 facilities and suppliers reported to the GHGRP, with 7,544 facilities reporting direct emissions totalling 2.58 billion metric tonnes CO2e across nine industry sectors.

**Access method:** EPA Envirofacts RESTful Data Service (https://enviro.epa.gov/efservice/). Programmatic JSON/CSV download by facility type, state, and subpart. FLIGHT web interface for visual inspection. Bulk CSV available at https://www.epa.gov/ghgreporting/data-sets.

**Key fields used by Fluxara:**
- `facility_id` — unique GHGRP identifier
- `facility_name`, `city`, `state`, `zip`, `county`
- `latitude`, `longitude` — facility centroid coordinates (decimal degrees, WGS84)
- `subpart_name` — reporting category (Subpart W: Petroleum and Natural Gas Systems)
- `ch4_quantity` — annual methane emissions in metric tonnes CO2e
- `reporting_year` — used to select most recent year for validation

**Licensing:** Public domain US government data. No access restrictions.

**Update cadence:** Annual release in October of each year (data from prior calendar year).

### 2.4 EU E-PRTR / Industrial Emissions Portal — EU Facility Registry

**Purpose:** EU equivalent of EPA GHGRP. Facility-level annual methane emission reports from EU oil and gas operators.

**Access method:** European Environment Agency (EEA) Industrial Emissions Portal API and bulk download at https://industry.eea.europa.eu. CSV/JSON downloads available by country, sector, and pollutant.

**Key fields:** Facility name, EEA facility ID, coordinates (latitude/longitude), reporting country, NACE sector code, annual CH4 emissions (kg/year).

**Update cadence:** Annual release (data from two years prior to release).

---

## 3. ALL PHYSICS FORMULAS WITH VARIABLE DEFINITIONS

### 3.1 Background Methane Removal

Before any attribution, each TROPOMI orbit is background-corrected to isolate enhancement signals above the baseline atmospheric XCH4:

**ΔXCHt(x, y) = XCH4(x, y) − XCH4_bg(x, y)**

Where:
- `ΔXCHt(x, y)` = XCH4 enhancement at pixel (x, y) in ppb
- `XCH4(x, y)` = bias-corrected TROPOMI methane column at pixel (x, y) in ppb
- `XCH4_bg(x, y)` = background XCH4 field, computed as the 15th percentile of `XCH4` values in a 200 km radius around pixel (x, y), excluding pixels within 20 km of known facility locations. Units: ppb

### 3.2 Cross-Sectional Flux (Gaussian Plume Mass Balance)

The Gaussian plume mass balance formula underpins both the synthetic training data generation and the physical interpretation of neural network outputs:

**Q = (M_CH4 / M_air) × ρ_air × U_eff × ∫∫ ΔXCHt(y, z) dy dz**

Where:
- `Q` = emission rate (kg/hr)
- `M_CH4` = molar mass of methane, 16.043 g/mol
- `M_air` = molar mass of dry air, 28.966 g/mol
- `ρ_air` = column air density (molecules/m²), computed from ERA5 surface pressure and temperature using ideal gas law: ρ_air = P_s / (R × T_2m) × N_A / M_air, where R = 8.314 J/(mol·K), N_A = 6.022 × 10²³ molecules/mol
- `U_eff` = effective wind speed perpendicular to the cross-section (m/s), from ERA5 interpolated to emission plume height (typically 0.5 × BLH)
- `∫∫ ΔXCHt(y, z) dy dz` = integrated XCH4 enhancement across a cross-section perpendicular to wind direction (ppb·m²)
- Integration is over spatial coordinates y (cross-wind) and z (vertical), approximated at TROPOMI resolution by summing pixel enhancements weighted by pixel area

**Simplified form used for neural network training label generation:**

**Q_simple = U_eff × L_plume × ΔXCHt_peak × (M_CH4 / M_air) × ρ_column × f_conversion**

Where:
- `L_plume` = characteristic plume width at TROPOMI resolution (m), defined as the spatial extent of pixels with `ΔXCHt > 0.5 × ΔXCHt_peak`
- `ΔXCHt_peak` = maximum enhancement within plume mask (ppb)
- `ρ_column` = dry air column density at TROPOMI pixel = P_s / (g × M_air) × N_A, where g = 9.81 m/s²
- `f_conversion` = unit conversion factor = 3600 s/hr (to convert m²/s to m²/hr)

### 3.3 Integrated Mass Enhancement (IME) — Alternative Quantification

**Q_IME = (M_CH4 / M_air) × U_eff × Σ_i [ΔXCHt_i × A_i] / τ_plume**

Where:
- `Σ_i [ΔXCHt_i × A_i]` = sum over all plume pixels i of (enhancement × pixel area) (ppb·m²)
- `τ_plume` = plume lifetime (s), approximated as L_plume / U_eff where L_plume is plume length in wind direction

The IME formula is used to cross-validate cross-sectional flux estimates and as a secondary training label for the neural network.

### 3.4 Planetary Boundary Layer Mixing

Emission rates are corrected for planetary boundary layer (PBL) depth, which sets the effective mixing volume:

**XCH4_surface(x, y) = ΔXCHt(x, y) × P_total / (P_PBL) × M_air / M_CH4**

Where:
- `P_total` = total atmospheric column pressure (Pa), from ERA5 `sp`
- `P_PBL` = pressure at top of PBL = P_s × exp(-BLH / H_scale), where BLH is ERA5 boundary layer height (m) and H_scale = 8,500 m is the atmospheric scale height

### 3.5 Uncertainty Propagation (Analytical)

Analytical uncertainty in emission rate Q from wind speed uncertainty σ_U and XCH4 retrieval uncertainty σ_Δ:

**σ_Q / Q = √[(σ_U / U_eff)² + (σ_Δ / ΔXCHt_peak)²]**

Where:
- `σ_U` = ERA5 wind speed uncertainty ≈ 10–15% of U_eff for flat terrain at boundary layer heights
- `σ_Δ` = TROPOMI XCH4 precision per pixel (typically 8–15 ppb; TROPOMI product provides `methane_mixing_ratio_precision`)

This analytical formula provides the expected error floor. The Bayesian MC Dropout uncertainty (Section 8) captures additional model uncertainty beyond this.

---

## 4. NEURAL NETWORK ARCHITECTURE SPECIFICATION

### 4.1 Architecture Class

**Architecture:** Modified U-Net with Residual Blocks and Dropout Layers (Bayesian U-Net)

**Reference architecture:** Ronneberger et al. (2015) U-Net, modified with:
- Residual connections within each encoder/decoder block (ResNet-style)
- Batch Normalisation after each convolutional layer
- Spatial Dropout (rate p = 0.2) applied at each block, active during both training AND inference (enabling MC Dropout)
- Multi-channel input (not single-image binary segmentation)
- Regression output (emission rate in kg/hr per facility) rather than pixel-wise segmentation

### 4.2 Input Tensor Specification

**Input shape:** (B, C, H, W) where:
- B = batch size (typically 4–8 for training, 1 for inference)
- C = 12 input channels (see below)
- H = 128 pixels (latitude dimension, covering ~700 km at TROPOMI 5.5 km resolution)
- W = 128 pixels (longitude dimension, covering ~900 km at TROPOMI 7 km resolution)

**Input channels (C = 12):**

| Channel | Variable | Source | Units | Preprocessing |
|---|---|---|---|---|
| 0 | XCH4 enhancement (ΔXCHt) | TROPOMI OFFL | ppb | Normalised to [0, 1] |
| 1 | XCH4 raw (bias-corrected) | TROPOMI OFFL | ppb | Normalised to [0, 1] |
| 2 | XCH4 retrieval precision | TROPOMI OFFL | ppb | Normalised to [0, 1] |
| 3 | QA value mask | TROPOMI OFFL | [0–1] | Binary threshold > 0.5 |
| 4 | ERA5 U-wind at 10 m | ERA5 | m/s | Normalised, range [−30, 30] |
| 5 | ERA5 V-wind at 10 m | ERA5 | m/s | Normalised, range [−30, 30] |
| 6 | ERA5 U-wind at 100 m | ERA5 | m/s | Normalised, range [−30, 30] |
| 7 | ERA5 V-wind at 100 m | ERA5 | m/s | Normalised, range [−30, 30] |
| 8 | ERA5 Boundary Layer Height | ERA5 | m | Normalised, range [0, 4000] |
| 9 | ERA5 Surface Pressure | ERA5 | Pa | Normalised, range [85000, 105000] |
| 10 | ERA5 2m Temperature | ERA5 | K | Normalised, range [240, 320] |
| 11 | Facility density map | GHGRP/E-PRTR | count/pixel | Binary: 1 = facility present, 0 = none |

All ERA5 variables are regridded from 0.25° to 0.05625° (matching TROPOMI overpass pixel spacing) using bilinear interpolation.

### 4.3 Output Tensor Specification

**Output shape:** (B, F) where:
- B = batch size
- F = maximum number of facilities per scene = 64 (zero-padded for scenes with fewer facilities)

**Output values:**
- Predicted emission rate per facility in kg/hr
- Values are log-transformed during training to handle the heavy-tailed emission distribution: `Q_pred = exp(y_pred)` where `y_pred` is the network output

**MC Dropout output:** For uncertainty quantification, the network performs N_samples = 50 stochastic forward passes with Dropout active. This produces:
- `Q_mean` = mean emission rate across 50 samples (kg/hr)
- `Q_std` = standard deviation across 50 samples (kg/hr)
- `Q_CI_95` = 95th percentile confidence interval = Q_mean ± 1.96 × Q_std

### 4.4 Encoder Architecture (Contracting Path)

The encoder consists of 4 resolution levels, each comprising a Residual Convolutional Block followed by MaxPooling:

**Level 1 (Input → 64 channels, H/1 × W/1):**
- Input: (B, 12, 128, 128)
- Conv2D(12 → 64, kernel=3×3, padding='same', stride=1)
- BatchNorm2D(64)
- ReLU activation
- Conv2D(64 → 64, kernel=3×3, padding='same', stride=1)
- BatchNorm2D(64)
- Residual addition: 1×1 Conv(12 → 64) + main path
- ReLU activation
- SpatialDropout2D(p=0.2)
- Output: (B, 64, 128, 128) → Skip connection saved → MaxPool2D(2×2) → (B, 64, 64, 64)

**Level 2 (64 → 128 channels, H/2 × W/2):**
- Input: (B, 64, 64, 64)
- Conv2D(64 → 128, 3×3, same)
- BatchNorm2D(128), ReLU
- Conv2D(128 → 128, 3×3, same)
- BatchNorm2D(128), Residual, ReLU
- SpatialDropout2D(p=0.2)
- Output: (B, 128, 64, 64) → Skip saved → MaxPool2D(2×2) → (B, 128, 32, 32)

**Level 3 (128 → 256 channels, H/4 × W/4):**
- Input: (B, 128, 32, 32)
- Conv2D(128 → 256, 3×3, same)
- BatchNorm2D(256), ReLU
- Conv2D(256 → 256, 3×3, same)
- BatchNorm2D(256), Residual, ReLU
- SpatialDropout2D(p=0.2)
- Output: (B, 256, 32, 32) → Skip saved → MaxPool2D(2×2) → (B, 256, 16, 16)

**Level 4 (256 → 512 channels, H/8 × W/8):**
- Input: (B, 256, 16, 16)
- Conv2D(256 → 512, 3×3, same)
- BatchNorm2D(512), ReLU
- Conv2D(512 → 512, 3×3, same)
- BatchNorm2D(512), Residual, ReLU
- SpatialDropout2D(p=0.2)
- Output: (B, 512, 16, 16) → Skip saved → MaxPool2D(2×2) → (B, 512, 8, 8)

### 4.5 Bottleneck

**Input:** (B, 512, 8, 8)
- Conv2D(512 → 1024, 3×3, same), BatchNorm, ReLU
- Conv2D(1024 → 1024, 3×3, same), BatchNorm, ReLU
- SpatialDropout2D(p=0.2)
- **Output:** (B, 1024, 8, 8)

Total bottleneck receptive field: each neuron sees approximately 180 × 180 pixels of the original 128 × 128 input at this stage.

### 4.6 Decoder Architecture (Expanding Path)

**Decoder Level 4 (1024 → 512, 8×8 → 16×16):**
- ConvTranspose2D(1024 → 512, kernel=2×2, stride=2) → upsample to (B, 512, 16, 16)
- Concatenate with Encoder Level 4 skip: → (B, 1024, 16, 16)
- Conv2D(1024 → 512, 3×3, same), BatchNorm, ReLU
- Conv2D(512 → 512, 3×3, same), BatchNorm, Residual, ReLU
- SpatialDropout2D(p=0.2)
- Output: (B, 512, 16, 16)

**Decoder Level 3 (512 → 256, 16×16 → 32×32):**
- ConvTranspose2D(512 → 256, 2×2, stride=2) → (B, 256, 32, 32)
- Concatenate with Encoder Level 3 skip → (B, 512, 32, 32)
- Conv2D × 2 + BatchNorm + Residual + Dropout
- Output: (B, 256, 32, 32)

**Decoder Level 2 (256 → 128, 32×32 → 64×64):**
- ConvTranspose2D(256 → 128, 2×2, stride=2) → (B, 128, 64, 64)
- Concatenate with Encoder Level 2 skip → (B, 256, 64, 64)
- Conv2D × 2 + BatchNorm + Residual + Dropout
- Output: (B, 128, 64, 64)

**Decoder Level 1 (128 → 64, 64×64 → 128×128):**
- ConvTranspose2D(128 → 64, 2×2, stride=2) → (B, 64, 128, 128)
- Concatenate with Encoder Level 1 skip → (B, 128, 128, 128)
- Conv2D × 2 + BatchNorm + Residual + Dropout
- Output: (B, 64, 128, 128)

### 4.7 Attribution Head (Spatial → Facility Vector)

Following the U-Net decoder, a facility attribution head converts the spatial feature map to per-facility emission predictions:

- **Facility feature extraction:** RoIAlign on each facility pixel location (from facility density map channel) → extracts 64-dimensional feature vector per facility
- **Facility MLP:** Linear(64 → 128) → ReLU → Dropout(0.2) → Linear(128 → 1) → output scalar log-emission rate per facility
- **Final activation:** Linear output (no activation); emission rate Q = exp(output) in kg/hr

### 4.8 Total Parameter Count

Estimated parameters:
- Encoder (Levels 1–4): ~14.7M
- Bottleneck: ~4.7M
- Decoder (Levels 4–1): ~10.9M
- Attribution Head: ~0.017M
- **Total: approximately 30M parameters**

This parameter count is computationally tractable for single A100 GPU inference and for training on a multi-GPU cluster with 4–8 GPUs.

### 4.9 Loss Function

The training loss is a composite of two terms:

**L_total = w1 × L_regression + w2 × L_physics**

**L_regression (Mean Squared Error in log space):**

L_regression = (1/N) × Σ_i (log(Q_pred_i + ε) − log(Q_true_i + ε))²

Where:
- N = number of facilities in batch with valid GHGRP labels
- ε = 1e-6 (numerical stability)
- Q_pred_i = predicted emission rate for facility i (kg/hr)
- Q_true_i = GHGRP-reported emission rate converted from annual tonnes to kg/hr (÷ 8,760)

**L_physics (Mass Balance Consistency):**

L_physics = | Σ_facilities Q_pred_i − Q_scene_total |² / Q_scene_total²

Where `Q_scene_total` is the total scene emission rate computed from the Gaussian plume formula applied to the observed XCH4 field. This physics loss penalises solutions where individual facility attributions do not sum to the independently derived total scene emission, improving physical consistency.

**Weights:** w1 = 0.8, w2 = 0.2 (tuned by validation set performance)

### 4.10 Training Procedure

**Optimiser:** AdamW (weight_decay = 1e-4), learning rate = 3e-4 with cosine annealing schedule (η_min = 1e-6, T_max = 100 epochs)

**Training data:** Synthetic plumes generated using the Gaussian plume formula applied to GHGRP-registered facility locations, superimposed onto real TROPOMI background fields. Training set: 2018–2022 TROPOMI orbits over US oil and gas basins (Permian, Anadarko, Appalachian, DJ, Bakken) and EU North Sea region. Approximately 50,000 scene/facility pairs.

**Validation data:** 2023 TROPOMI orbits over held-out facilities not used in training. Approximately 8,000 scene/facility pairs.

**Test data:** 2024 TROPOMI orbits with independent cross-validation against MethaneSAT and aircraft mass balance measurements where available.

**Batch size:** 4 scenes per GPU × 4 GPUs = effective batch size of 16

**Training duration (estimated):** 100 epochs × ~3,125 steps/epoch = ~312,500 steps. At ~0.5s/step on 4× A100 GPUs: approximately 43 hours total training time.

**Data augmentation:** Random horizontal/vertical flips, random rotation ±15°, random wind direction perturbation ±20°, random XCH4 noise addition (σ = 5 ppb), cloud mask simulation (random rectangular masking of 0–30% of pixels).

---

## 5. COMPLETE DATA PIPELINE

### 5.1 Stage 1 — TROPOMI Ingest

**Trigger:** Daily scheduled job (06:00 UTC) or on-demand API request

**Process:**
1. Query Copernicus Data Space Ecosystem API for new OFFL L2__CH4___ granules covering target bounding boxes (US oil basins, North Sea, Caspian region)
2. Download NetCDF4 granules via HTTPS (≈82 MB per granule, 14 granules/day globally → 1.1 GB/day)
3. Parse NetCDF4 using `xarray` (version ≥ 2024.1) and `h5netcdf` (version ≥ 1.3.0)
4. Apply quality filter: retain pixels where `qa_value > 0.5` and `solar_zenith_angle < 70°`
5. Extract variables: `methane_mixing_ratio_bias_corrected`, `methane_mixing_ratio_precision`, `qa_value`, `latitude`, `longitude`, `latitude_bounds`, `longitude_bounds`
6. Regrid to regular 0.05° × 0.05° grid using area-weighted averaging via `pyresample` (version ≥ 1.28.0)
7. Compute background field (15th percentile in 200 km sliding window) using `scipy.ndimage.uniform_filter`
8. Compute XCH4 enhancement: `delta_xch4 = xch4_bias_corrected − xch4_background`
9. Write processed daily composite to internal GeoTIFF via `rasterio` (version ≥ 1.3.9)

**Output:** Daily 0.05° XCH4 enhancement rasters, one per target basin, stored in cloud object storage (GCS or AWS S3)

### 5.2 Stage 2 — ERA5 Ingest

**Trigger:** Daily scheduled job (07:00 UTC, 1 hour after TROPOMI ingest)

**Process:**
1. Request ERA5 hourly data via `cdsapi` (version ≥ 0.7.0) for the TROPOMI overpass time (13:00–14:00 local solar time, converted to UTC per target region)
2. Download NetCDF via CDS API, bounding box clipped to target region ± 2° margin
3. Parse with `xarray`, regrid from 0.25° to 0.05° using bilinear interpolation via `xarray.interp`
4. Temporal interpolation to exact TROPOMI overpass time (linear between surrounding hourly fields)
5. Compute derived variables: effective wind speed at plume height (0.5 × BLH), wind direction
6. Write ERA5 wind composites aligned to TROPOMI grid → GeoTIFF

**Output:** ERA5 wind field rasters at TROPOMI spatial resolution, time-matched to overpass

### 5.3 Stage 3 — Facility Database Alignment

**Trigger:** Daily (for US GHGRP) or annual update (for E-PRTR)

**Process:**
1. Query EPA GHGRP Envirofacts REST API: GET `https://enviro.epa.gov/efservice/PUB_DIM_FACILITY/JSON` filtered by subpart=W (oil and gas) → parse facility list with coordinates
2. For EU: load E-PRTR CSV from EEA Industrial Emissions Portal
3. Spatial index construction using `rtree` (version ≥ 1.2.0) for fast lookup of facilities within TROPOMI scene extent
4. Generate facility density map: binary raster at 0.05° resolution, 1 = facility centroid within pixel
5. Cache facility database in PostgreSQL 16 (see Section 7, Database Schema)

### 5.4 Stage 4 — Input Tensor Assembly

**Process:**
1. For each target scene bounding box (1,000 × 1,000 km, ~128 × 128 pixels at 0.05°):
   - Load TROPOMI XCH4 enhancement raster (channels 0–1)
   - Load TROPOMI precision and QA rasters (channels 2–3)
   - Load ERA5 wind fields (channels 4–9)
   - Generate facility density map (channel 10→11 including surface pressure/temperature)
2. Stack into tensor shape (12, 128, 128)
3. Apply per-channel normalisation using precomputed training-set statistics (mean, std stored in `config/normalisation_stats.json`)
4. Batch assembly: group 4 scenes into batch (4, 12, 128, 128)

### 5.5 Stage 5 — Neural Network Inference

**Hardware:** Single NVIDIA A100 40GB GPU (production), or single A10 24GB GPU (cost-optimised deployment)

**Process:**
1. Load model weights from `model/fluxara_v1.pt` (PyTorch checkpoint, ≈120 MB)
2. Set model to `eval()` mode but with Dropout ENABLED (MC Dropout inference)
3. Run N_samples = 50 stochastic forward passes on single GPU:
   - Each pass: (4, 12, 128, 128) → encoder → bottleneck → decoder → attribution head → (4, 64) emission vector
   - 50 passes × 4 scenes each = 200 total forward passes
   - GPU wall-clock time: ≈4 seconds on A100 at FP16 precision (using `torch.cuda.amp` automatic mixed precision)
4. Aggregate: compute Q_mean, Q_std per facility across 50 samples
5. Total inference time including data loading and pre/post-processing: **≤ 8 seconds**

**Framework:** PyTorch 2.3.0 (CUDA 12.1), deployed in Docker container via TorchServe 0.10.0

### 5.6 Stage 6 — Attribution Assignment

**Process:**
1. Match facility indices in output vector to GHGRP/E-PRTR facility IDs via lookup table generated in Stage 3
2. Apply de-duplication: if multiple GHGRP facilities fall within same 0.05° pixel, distribute attributed emission proportional to reported prior year emissions
3. Filter out facilities with `Q_mean < 5 kg/hr` (below TROPOMI detection threshold)
4. Flag attributions where `Q_std / Q_mean > 0.5` as high-uncertainty (> 50% coefficient of variation)

### 5.7 Stage 7 — Report Generation

**Process:**
1. Populate report template with attribution results using `Jinja2` (version ≥ 3.1.4) HTML template engine
2. Convert HTML to PDF using `WeasyPrint` (version ≥ 61.0) for regulatory report output
3. Report contents (see Section 9 for full API response schema):
   - Facility name, ID, location, operator
   - Attribution date and TROPOMI orbit ID
   - Q_mean (kg/hr), Q_std (kg/hr), 95% CI bounds
   - Comparison to most recent GHGRP annual reported rate
   - Methane column enhancement map (PNG) with facility overlay
   - Wind field visualisation
   - Uncertainty classification (low/medium/high)
   - Methodology statement and data source citations
4. Upload PDF to secure cloud storage → generate signed URL for customer API delivery

---

## 6. TECHNOLOGY STACK

| Component | Technology | Version | Justification |
|---|---|---|---|
| Core ML framework | PyTorch | 2.3.0 | CUDA 12.1 support; production-grade TorchServe deployment; largest ML ecosystem |
| GPU compute | NVIDIA A100 40GB | — | FP16 mixed precision; fastest available for transformer-style networks; A10 for cost-optimised |
| Satellite data parsing | xarray + h5netcdf | 2024.1 / 1.3.0 | Native NetCDF4 support; lazy loading for large TROPOMI granules |
| Regridding | pyresample | 1.28.0 | Area-weighted regridding standard for satellite data; ESA-maintained |
| Meteorological data | cdsapi | 0.7.0 | Official ECMWF CDS API client |
| Spatial indexing | rtree + shapely | 1.2.0 / 2.0.6 | Fast facility geolocation queries |
| Geospatial raster I/O | rasterio | 1.3.9 | GeoTIFF read/write; CRS management |
| Database | PostgreSQL | 16.0 | Structured facility data and job queue |
| Database ORM | SQLAlchemy | 2.0.36 | Async support for FastAPI |
| API framework | FastAPI | 0.115 | Async Python; OpenAPI auto-documentation; production-grade |
| API deployment | Uvicorn + Gunicorn | 0.30.0 / 22.0 | ASGI server for FastAPI |
| Model serving | TorchServe | 0.10.0 | Batched inference; health endpoints; GPU management |
| Report generation | WeasyPrint | 61.0 | HTML → PDF; CSS support; no browser dependency |
| Templating | Jinja2 | 3.1.4 | Report templates |
| Cloud storage | AWS S3 / GCS | — | Satellite data archive; report delivery |
| Container | Docker | 25.0 | Reproducible builds |
| Orchestration | AWS ECS Fargate / Cloud Run | — | Serverless containers for API; no idle GPU cost |
| Monitoring | Prometheus + Grafana | 2.51 / 10.4 | Inference latency, throughput, and accuracy tracking |
| CI/CD | GitHub Actions | — | Automated tests and model evaluation on push |
| Scientific Python | NumPy / SciPy / Pandas | 1.26 / 1.13 / 2.2 | Numerical computing |
| Visualisation | Matplotlib / Cartopy | 3.8 / 0.23 | Geospatial plotting for reports |

---

## 7. DATABASE SCHEMA

### 7.1 Core Tables (PostgreSQL 16)

**Table: facilities**
```
facility_id          VARCHAR(50)   PRIMARY KEY    -- GHGRP facility ID or E-PRTR ID
facility_name        VARCHAR(255)  NOT NULL
operator_name        VARCHAR(255)
registry             ENUM('GHGRP', 'E-PRTR')     NOT NULL
latitude             FLOAT         NOT NULL        -- WGS84 decimal degrees
longitude            FLOAT         NOT NULL        -- WGS84 decimal degrees
country              VARCHAR(3)                   -- ISO 3166-1 alpha-3
state_region         VARCHAR(50)
sector_code          VARCHAR(20)                  -- NAICS (US) or NACE (EU)
subpart              VARCHAR(10)                  -- e.g., 'W' for O&G
last_reported_ch4_tpy FLOAT                      -- tonnes CH4/year (most recent report)
last_report_year     INTEGER
created_at           TIMESTAMPTZ   DEFAULT NOW()
updated_at           TIMESTAMPTZ   DEFAULT NOW()
```

**Table: attributions**
```
attribution_id       UUID          PRIMARY KEY    DEFAULT gen_random_uuid()
facility_id          VARCHAR(50)   REFERENCES facilities(facility_id)
orbit_id             VARCHAR(100)  NOT NULL       -- TROPOMI orbit identifier
scene_date           DATE          NOT NULL       -- date of TROPOMI overpass
inference_timestamp  TIMESTAMPTZ   NOT NULL       -- when inference ran
q_mean_kghr          FLOAT         NOT NULL       -- emission rate, mean (kg/hr)
q_std_kghr           FLOAT         NOT NULL       -- emission rate, std dev (kg/hr)
q_ci95_lower         FLOAT                       -- 95% CI lower bound (kg/hr)
q_ci95_upper         FLOAT                       -- 95% CI upper bound (kg/hr)
delta_xch4_ppb       FLOAT                       -- peak XCH4 enhancement (ppb)
wind_speed_ms        FLOAT                       -- effective wind speed (m/s)
wind_direction_deg   FLOAT                       -- wind direction (degrees from N)
blh_m                FLOAT                       -- boundary layer height (m)
qa_coverage_pct      FLOAT                       -- % valid TROPOMI pixels in scene
uncertainty_class    ENUM('LOW','MEDIUM','HIGH')
model_version        VARCHAR(20)   NOT NULL       -- e.g., 'v1.2.0'
report_url           TEXT                        -- signed URL to PDF report
created_at           TIMESTAMPTZ   DEFAULT NOW()
```

**Table: scenes**
```
scene_id             UUID          PRIMARY KEY    DEFAULT gen_random_uuid()
orbit_id             VARCHAR(100)  NOT NULL
scene_date           DATE          NOT NULL
bbox_north           FLOAT         NOT NULL
bbox_south           FLOAT         NOT NULL
bbox_east            FLOAT         NOT NULL
bbox_west            FLOAT         NOT NULL
tropomi_granule_path TEXT          NOT NULL       -- S3/GCS path to source NetCDF4
era5_wind_path       TEXT          NOT NULL       -- S3/GCS path to ERA5 NetCDF
valid_pixel_pct      FLOAT                       -- fraction of qa > 0.5 pixels
cloud_cover_pct      FLOAT
total_scene_q_kghr   FLOAT                       -- total scene emission (Gaussian)
processing_status    ENUM('PENDING','RUNNING','COMPLETE','FAILED')
processing_time_s    FLOAT                       -- wall-clock inference time
created_at           TIMESTAMPTZ   DEFAULT NOW()
```

**Table: customers**
```
customer_id          UUID          PRIMARY KEY    DEFAULT gen_random_uuid()
company_name         VARCHAR(255)  NOT NULL
contact_email        VARCHAR(255)  NOT NULL
api_key_hash         VARCHAR(64)   NOT NULL       -- SHA-256 hash of API key
plan                 ENUM('TRIAL','BASIC','PRO','ENTERPRISE')
facilities_subscribed TEXT[]                     -- array of facility_ids
rate_limit_rpm       INTEGER       DEFAULT 60
created_at           TIMESTAMPTZ   DEFAULT NOW()
```

**Indexes:**
- `CREATE INDEX idx_attributions_facility_date ON attributions(facility_id, scene_date DESC)`
- `CREATE INDEX idx_attributions_scene ON attributions(orbit_id)`
- `CREATE INDEX idx_facilities_geo ON facilities USING GIST (ll_to_earth(latitude, longitude))`
- `CREATE INDEX idx_scenes_date ON scenes(scene_date DESC)`

---

## 8. API ENDPOINT SPECIFICATIONS

**Base URL:** `https://api.fluxara.io/v1`

**Authentication:** Bearer token (JWT) in `Authorization` header

**Rate limiting:** Plan-dependent; 60 requests/minute (Basic), 300 requests/minute (Pro), unlimited (Enterprise)

---

**GET /attributions/{facility_id}**

Returns emission attribution history for a specific facility.

Parameters:
- `facility_id` (path, required): GHGRP or E-PRTR facility identifier
- `start_date` (query, optional): ISO 8601 date, default = 30 days ago
- `end_date` (query, optional): ISO 8601 date, default = today
- `limit` (query, optional): integer 1–365, default = 30

Response (200 OK):
```json
{
  "facility_id": "1002342",
  "facility_name": "Permian Basin Compressor Station 14",
  "operator": "Pioneer Natural Resources",
  "registry": "GHGRP",
  "coordinates": {"lat": 31.8452, "lon": -102.3317},
  "attributions": [
    {
      "attribution_id": "uuid",
      "scene_date": "2026-06-01",
      "orbit_id": "S5P_OFFL_L2__CH4____20260601T...",
      "q_mean_kghr": 847.3,
      "q_std_kghr": 112.6,
      "q_ci95_lower": 626.6,
      "q_ci95_upper": 1068.0,
      "delta_xch4_ppb": 24.7,
      "wind_speed_ms": 4.2,
      "uncertainty_class": "MEDIUM",
      "report_url": "https://reports.fluxara.io/signed/..."
    }
  ],
  "ghgrp_reported_kghr": 312.4,
  "ratio_satellite_to_reported": 2.71
}
```

---

**GET /scenes/{scene_date}**

Returns all attributions for all facilities within a basin on a given date.

Parameters:
- `scene_date` (path, required): ISO 8601 date
- `basin` (query, optional): enum `permian | marcellus | anadarko | bakken | north_sea | caspian`
- `min_emission_kghr` (query, optional): float, filter threshold

Response (200 OK): Array of attribution objects as above.

---

**POST /reports/generate**

Triggers on-demand generation of an MRV report for a specific facility and date range.

Request body:
```json
{
  "facility_id": "1002342",
  "start_date": "2026-01-01",
  "end_date": "2026-06-30",
  "report_format": "pdf",
  "regulatory_framework": "EU_METHANE_REG"
}
```

Response (202 Accepted): `{ "job_id": "uuid", "estimated_completion_s": 45 }`

**GET /reports/{job_id}** — Poll for report completion; returns signed URL when ready.

---

**GET /health**

Internal health check endpoint. Returns `{"status": "ok", "model_version": "v1.2.0", "gpu_available": true, "inference_latency_p99_s": 7.3}`

---

**GET /facilities/search**

Search facility registry by location or name.

Parameters: `lat`, `lon`, `radius_km`, `name_query`, `registry` (GHGRP or E-PRTR)

---

## 9. BAYESIAN UNCERTAINTY QUANTIFICATION — TECHNICAL DETAIL

Fluxara implements Monte Carlo Dropout as an approximation to Bayesian inference, as formalized by Gal & Ghahramani (2016). During inference, Spatial Dropout (p = 0.2) is applied at each residual block in both encoder and decoder. N_samples = 50 stochastic forward passes are executed per scene.

**Output statistics computed:**

Q_samples = {Q¹, Q², ..., Q⁵⁰} — set of 50 emission predictions per facility

Q_mean = (1/50) × Σ Q^k

Q_var = (1/50) × Σ (Q^k − Q_mean)² + σ²_aleatoric

Where σ²_aleatoric is the inherent measurement noise estimated from the XCH4 precision field, propagated through the network as an auxiliary output head trained on known measurement uncertainties.

Q_std = √Q_var

**Uncertainty classification thresholds:**
- `LOW`: Q_std / Q_mean < 0.15 (coefficient of variation < 15%)
- `MEDIUM`: 0.15 ≤ Q_std / Q_mean < 0.40
- `HIGH`: Q_std / Q_mean ≥ 0.40

**Practical interpretation:**
- `LOW` uncertainty: attribution suitable for regulatory submission without further verification
- `MEDIUM` uncertainty: attribution suitable for screening and trend analysis; recommend LDAR cross-check for regulatory use
- `HIGH` uncertainty: typically caused by cloud cover (< 30% valid pixels), low wind speed (< 1.5 m/s, causing plume stagnation), or facility within dense industrial cluster

The additional wall-clock cost of 50 forward passes versus 1 is approximately 45 additional milliseconds per scene on an A100 GPU (GPU memory-bound for this batch size, not compute-bound), making MC Dropout uncertainty quantification essentially free at inference time.

---

## 10. PERFORMANCE SPECIFICATIONS SUMMARY

| Metric | Target | Method of Measurement |
|---|---|---|
| Inference time (1 basin, 1 day) | ≤ 8 seconds | Wall clock from tensor assembly to Q_mean output |
| Attribution accuracy | 86% | Fraction of scenes where highest-predicted facility matches STILT-derived top emitter |
| Mean Absolute Error vs GHGRP | 14% | MAE of (Q_mean_annual − Q_ghgrp_annual) / Q_ghgrp_annual on held-out 2023 validation set |
| Speedup vs STILT (4 hr baseline) | 1,801× | 14,400 seconds / 8 seconds |
| MC Dropout uncertainty (50 samples) | < 0.5s overhead | Per 50-sample batch on A100 |
| API response time (attribution lookup) | < 200 ms | Database query + serialisation, no inference required |
| Report generation (PDF) | < 60 seconds | Jinja2 + WeasyPrint render time |
| Data pipeline latency (OFFL) | 5–7 days | TROPOMI OFFL availability constraint |
| Model checkpoint size | ~120 MB | PyTorch FP32 weights |
| Daily compute cost (10 basins) | ~$8–12 USD | A100 spot instance, 10 × 8s inference + pipeline |

---

## 11. DATA LICENSING SUMMARY

| Source | Cost | License | Commercial Use |
|---|---|---|---|
| TROPOMI L2 CH4 (Copernicus) | Free | Copernicus Open Licence | Yes |
| ERA5 (ECMWF CDS) | Free | Copernicus Licence | Yes |
| EPA GHGRP data | Free | US Government public domain | Yes |
| EU E-PRTR / EEA Industrial Emissions | Free | EEA standard licence | Yes |
| PyTorch | Free | BSD 3-Clause | Yes |
| FastAPI | Free | MIT | Yes |
| PostgreSQL | Free | PostgreSQL Licence | Yes |

All primary data inputs and all software dependencies are free, open-source, or open-data. Fluxara has zero marginal data cost per scene processed.

---

*End of Document 3 — Full Technical Specification*
