# database/seed.py
import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fluxara.database.connection import AsyncSessionLocal, engine
from sqlalchemy import text

FACILITIES = [
    {"name": "Pioneer Natural Resources - Spraberry", "lat": 31.85, "lon": -102.10, "state": "TX", "epa": 450.5, "risk": "low", "sector": "oil_gas", "ghgrp": "1001234"},
    {"name": "Occidental Petroleum - Delaware Basin",  "lat": 31.90, "lon": -102.30, "state": "TX", "epa": 1200.2, "risk": "high", "sector": "oil_gas", "ghgrp": "1005678"},
    {"name": "ConocoPhillips - Midland Basin",         "lat": 32.10, "lon": -102.50, "state": "TX", "epa": 850.0, "risk": "medium", "sector": "oil_gas", "ghgrp": "1009012"},
    {"name": "ExxonMobil - XTO Permian",               "lat": 31.70, "lon": -102.20, "state": "TX", "epa": 2100.8, "risk": "high", "sector": "oil_gas", "ghgrp": "1003456"},
    {"name": "Chevron - Permian Operations",           "lat": 32.20, "lon": -101.90, "state": "TX", "epa": 320.4, "risk": "low", "sector": "oil_gas", "ghgrp": "1007890"},
]

async def seed_data():
    async with AsyncSessionLocal() as session:
        print("🌱 Seeding facilities...")
        for f in FACILITIES:
            # Note: ST_SetSRID(ST_Point(lon, lat), 4326) for location
            # We use text() to execute raw SQL for spatial columns easily
            query = text("""
                INSERT INTO facilities (name, lat, lon, state, epa_reported, risk_level, sector, ghgrp_id, location)
                VALUES (:name, :lat, :lon, :state, :epa, :risk, :sector, :ghgrp, ST_SetSRID(ST_Point(:lon, :lat), 4326))
                ON CONFLICT DO NOTHING;
            """)
            await session.execute(query, f)
        
        print("🌱 Seeding alerts...")
        alerts = [
            {"facility_id": 2, "type": "spike", "severity": "high", "message": "Sudden 40% increase in methane concentration detected over Delaware Basin.", "val": 1680.5, "thresh": 1200.0},
            {"facility_id": 4, "type": "anomaly", "severity": "medium", "message": "Unusual emission pattern detected at XTO Permian site.", "val": 2400.0, "thresh": 2100.0}
        ]
        for a in alerts:
            await session.execute(text("""
                INSERT INTO alerts (facility_id, alert_type, severity, message, emission_value, threshold_value)
                VALUES (:facility_id, :type, :severity, :message, :val, :thresh);
            """), a)

        print("🌱 Seeding reports...")
        reports = [
            {"facility_id": 1, "type": "mrv", "status": "verified", "total": 12450.5},
            {"facility_id": 3, "type": "compliance", "status": "pending", "total": 8900.2},
            {"facility_id": 5, "type": "carbon_credit", "status": "verified", "total": 450.0}
        ]
        for r in reports:
            await session.execute(text("""
                INSERT INTO reports (facility_id, report_type, status, total_emissions, date_from, date_to)
                VALUES (:facility_id, :type, :status, :total, '2024-01-01', '2024-01-31');
            """), r)
        
        print("🌱 Seeding users...")
        users = [
            {"email": "admin@fluxara.ai", "company": "Fluxara", "role": "admin", "key": "fluxara-dev-key-2024"},
            {"email": "operator@pioneer.com", "company": "Pioneer Natural Resources", "role": "operator", "key": "pioneer-key-7788"}
        ]
        for u in users:
            await session.execute(text("""
                INSERT INTO users (email, company, role, api_key)
                VALUES (:email, :company, :role, :key);
            """), u)

        await session.commit()
        print("✅ Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_data())
