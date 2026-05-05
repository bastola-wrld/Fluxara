# fluxara/database/init_db.py
from fluxara.database.connection import engine, SessionLocal
from fluxara.database.models import Base
from fluxara.database.crud import create_user, create_api_key, create_facility

def init():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")

    db = SessionLocal()
    try:
        # Seed admin user
        user = create_user(db, name="Fluxara Admin",
                           email="admin@fluxara.ai", org="Fluxara")
        print(f"✅ Admin user created: {user.email}")

        # Seed dev API key
        create_api_key(db, key="fluxara-dev-key-2024",
                       name="Dev Key", user_id=user.id, permissions="admin")
        print("✅ Dev API key seeded")

        # Seed Permian Basin facilities
        facilities = [
            ("Pioneer Natural Resources - Spraberry", 31.85, -102.10, "TX", 300000, "high"),
            ("Occidental Petroleum - Delaware Basin",  31.90, -102.30, "TX", 350000, "high"),
            ("ConocoPhillips - Midland Basin",         32.10, -102.50, "TX", 250000, "medium"),
            ("ExxonMobil - XTO Permian",               31.70, -102.20, "TX", 200000, "low"),
            ("Chevron - Permian Operations",           32.20, -101.90, "TX", 150000, "low"),
        ]
        for name, lat, lon, state, epa, risk in facilities:
            create_facility(db, name=name, lat=lat, lon=lon,
                            state=state, epa_reported_kgh=epa, risk_level=risk)
        print(f"✅ {len(facilities)} facilities seeded")

    finally:
        db.close()
    print("\n🚀 Database ready!")

if __name__ == "__main__":
    init()