-- database/schema.sql

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- TABLE: facilities
CREATE TABLE IF NOT EXISTS facilities (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    state           VARCHAR(2),
    country         VARCHAR(3) DEFAULT 'USA',
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    location        GEOGRAPHY(POINT, 4326),  -- PostGIS spatial column
    epa_reported    DOUBLE PRECISION,        -- kg/hr self-reported
    fluxara_latest  DOUBLE PRECISION,        -- kg/hr our estimate
    risk_level      VARCHAR(10),             -- high/medium/low
    sector          VARCHAR(50),             -- oil_gas/agriculture/industrial
    ghgrp_id        VARCHAR(50),             -- EPA GHGRP identifier
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- TABLE: inversions
CREATE TABLE IF NOT EXISTS inversions (
    id              SERIAL PRIMARY KEY,
    facility_id     INTEGER REFERENCES facilities(id),
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    date            DATE NOT NULL,
    emission_rate   DOUBLE PRECISION,        -- kg/hr result
    uncertainty     DOUBLE PRECISION,        -- 1-sigma kg/hr
    confidence      DOUBLE PRECISION,        -- 0-1 score
    compute_ms      INTEGER,                 -- milliseconds taken
    tropomi_file    VARCHAR(255),            -- source data file
    era5_file       VARCHAR(255),            -- wind data file
    created_at      TIMESTAMP DEFAULT NOW()
);

-- TABLE: alerts
CREATE TABLE IF NOT EXISTS alerts (
    id              SERIAL PRIMARY KEY,
    facility_id     INTEGER REFERENCES facilities(id),
    alert_type      VARCHAR(50),   -- spike/anomaly/threshold_breach/offline
    severity        VARCHAR(10),   -- high/medium/low
    message         TEXT,
    emission_value  DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    resolved        BOOLEAN DEFAULT FALSE,
    resolved_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- TABLE: reports
CREATE TABLE IF NOT EXISTS reports (
    id              SERIAL PRIMARY KEY,
    facility_id     INTEGER REFERENCES facilities(id),
    report_type     VARCHAR(50),   -- mrv/compliance/carbon_credit
    date_from       DATE,
    date_to         DATE,
    total_emissions DOUBLE PRECISION,
    status          VARCHAR(20),   -- pending/verified/rejected
    pdf_path        VARCHAR(255),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- TABLE: users
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    company         VARCHAR(255),
    role            VARCHAR(20),   -- admin/operator/viewer
    api_key         VARCHAR(64) UNIQUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- TABLE: generated_reports (admin-generated PDFs stored as binary)
CREATE TABLE IF NOT EXISTS generated_reports (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    report_type     VARCHAR(50) NOT NULL,   -- summary/full/compliance
    region          VARCHAR(100),           -- country code or 'Global'
    org_id          INTEGER REFERENCES organisations(id),
    facility_id     INTEGER REFERENCES facilities(id),
    date_from       DATE,
    date_to         DATE,
    total_facilities INTEGER,
    total_emissions DOUBLE PRECISION,
    pdf_data        BYTEA NOT NULL,         -- binary PDF content
    file_size       INTEGER,
    generated_by    INTEGER REFERENCES users(id),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- PostGIS spatial index
CREATE INDEX IF NOT EXISTS facilities_location_idx 
ON facilities USING GIST(location);
