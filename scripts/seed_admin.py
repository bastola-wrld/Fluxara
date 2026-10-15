#!/usr/bin/env python3
"""
Create or update the first admin user.

    FLUXARA_ADMIN_EMAIL=you@example.com FLUXARA_ADMIN_PASSWORD='a long passphrase' \\
        python scripts/seed_admin.py

There is no default password. The password must be at least 12 characters.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fluxara.api.auth import get_password_hash        # noqa: E402
from fluxara.database.models import User              # noqa: E402
from fluxara.database.sync import session_scope       # noqa: E402


def main():
    email = os.getenv("FLUXARA_ADMIN_EMAIL")
    password = os.getenv("FLUXARA_ADMIN_PASSWORD")
    if not email or not password:
        sys.exit("Set FLUXARA_ADMIN_EMAIL and FLUXARA_ADMIN_PASSWORD.")
    if len(password) < 12:
        sys.exit("FLUXARA_ADMIN_PASSWORD must be at least 12 characters.")
    with session_scope() as db:
        user = db.query(User).filter(User.email == email).one_or_none()
        if user:
            user.hashed_password = get_password_hash(password)
            user.role, user.active = "admin", True
            print(f"Updated admin {email}")
        else:
            db.add(User(email=email, hashed_password=get_password_hash(password),
                        role="admin", company="Fluxara", active=True))
            print(f"Created admin {email}")


if __name__ == "__main__":
    main()
