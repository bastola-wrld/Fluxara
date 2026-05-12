import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy.future import select
from fluxara.database.connection import AsyncSessionLocal
from fluxara.database.models import User
from fluxara.api.auth import get_password_hash

async def seed():
    async with AsyncSessionLocal() as db:
        # Check if admin exists
        result = await db.execute(select(User).where(User.email == "admin@fluxara.io"))
        user = result.scalar_one_or_none()
        
        if user:
            user.hashed_password = get_password_hash("fluxaraadmin123")
            print("Updated existing admin password for admin@fluxara.io")
        else:
            user = User(
                email="admin@fluxara.io",
                hashed_password=get_password_hash("fluxaraadmin123"),
                role="admin",
                company="Fluxara",
                active=True
            )
            db.add(user)
            print("Created new admin user admin@fluxara.io")
            
        await db.commit()

if __name__ == "__main__":
    asyncio.run(seed())
