# scripts/reset_db.py
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from fluxara.database.connection import engine, AsyncSessionLocal
from fluxara.database.models import Base, User
from fluxara.api.auth import get_password_hash
from sqlalchemy import text

async def reset():
    print("⚠️  Dropping all tables to sync schema...")
    async with engine.begin() as conn:
        # Drop all tables including spatial ones
        await conn.run_sync(Base.metadata.drop_all)
        # Recreate everything fresh
        await conn.run_sync(Base.metadata.create_all)
    
    print("🌱 Seeding admin user...")
    async with AsyncSessionLocal() as db:
        admin = User(
            email="admin@fluxara.io",
            hashed_password=get_password_hash("fluxaraadmin123"),
            role="admin",
            company="Fluxara",
            active=True
        )
        db.add(admin)
        await db.commit()
    
    print("✅ Database reset and admin@fluxara.io created!")

if __name__ == "__main__":
    asyncio.run(reset())
