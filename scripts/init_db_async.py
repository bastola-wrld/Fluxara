#!/usr/bin/env python3
"""
Fluxara DB Bootstrap — async, works without PostGIS.
Run: python scripts/init_db_async.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Pull DB URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://mqc@localhost:5432/fluxara"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def ensure_db_exists():
    """Create the fluxara database if it doesn't exist."""
    # Connect to postgres (default db) to create fluxara
    base_url = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_async_engine(base_url, isolation_level="AUTOCOMMIT", echo=False)
    try:
        async with admin_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname='fluxara'")
            )
            exists = result.fetchone()
            if not exists:
                await conn.execute(text("CREATE DATABASE fluxara"))
                print("✅ Created database: fluxara")
            else:
                print("✅ Database 'fluxara' already exists")
    except Exception as e:
        print(f"⚠️  Could not auto-create DB: {e}")
        print("   → Assuming 'fluxara' DB already exists and continuing...")
    finally:
        await admin_engine.dispose()


async def init():
    await ensure_db_exists()

    # Import models after DB URL is set
    from fluxara.database.connection import Base
    import fluxara.database.models  # noqa: register all models

    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created/verified")

    # Seed data
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count > 0:
            print(f"✅ Already seeded ({count} users found). Skipping.")
            return

        # Seed admin user
        await db.execute(text("""
            INSERT INTO users (email, company, role, api_key, created_at)
            VALUES ('admin@fluxara.ai', 'Fluxara', 'admin', 'fluxara-dev-key-2024', NOW())
            ON CONFLICT (email) DO NOTHING
        """))

        # Seed 10 Permian Basin facilities (real-world coordinates)
        facilities = [
            ("Pioneer Natural Resources - Spraberry",     31.850, -102.100, "TX", 847300, "high"),
            ("Occidental Petroleum - Delaware Basin",     31.900, -102.300, "TX", 920000, "high"),
            ("ConocoPhillips - Midland Basin",            32.100, -102.500, "TX", 620000, "medium"),
            ("ExxonMobil - XTO Permian",                  31.700, -102.200, "TX", 480000, "medium"),
            ("Chevron - Permian Operations",              32.200, -101.900, "TX", 380000, "low"),
            ("Devon Energy - Delaware Basin",             31.600, -102.400, "TX", 710000, "high"),
            ("Diamondback Energy - Midland",              32.000, -102.000, "TX", 310000, "medium"),
            ("Coterra Energy - Permian",                  31.800, -102.600, "TX", 290000, "low"),
            ("Marathon Oil - Permian Basin",              32.300, -102.200, "TX", 540000, "medium"),
            ("Apache Corporation - Alpine High",          30.900, -104.100, "TX", 660000, "high"),
        ]
        for name, lat, lon, state, epa, risk in facilities:
            await db.execute(text("""
                INSERT INTO facilities (name, lat, lon, state, country, epa_reported, risk_level, created_at, updated_at)
                VALUES (:name, :lat, :lon, :state, 'USA', :epa, :risk, NOW(), NOW())
                ON CONFLICT DO NOTHING
            """), {"name": name, "lat": lat, "lon": lon, "state": state, "epa": epa, "risk": risk})

        # Seed some sample alerts
        await db.execute(text("""
            INSERT INTO alerts (facility_id, alert_type, severity, message, emission_value, threshold_value, resolved, created_at)
            SELECT id, 'emission_spike', 'critical',
                   'Methane emission 40% above EPA reported baseline',
                   epa_reported * 1.4, epa_reported, false, NOW()
            FROM facilities WHERE risk_level = 'high'
            LIMIT 3
        """))

        await db.commit()
        print("✅ Seeded 1 user + 10 Permian Basin facilities + 3 alerts")

    print("\n🚀 Fluxara database ready!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init())
