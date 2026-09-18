"""
Bootstrap script: creates tables (if using SQLite) and seeds an admin
account plus a handful of sample charities, so the app is immediately
usable for a demo/review without any manual data entry.

Run from backend/: venv/Scripts/python.exe seed.py
"""
import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.db import AsyncSessionLocal, init_db
from app.models.charity import Charity
from app.models.user import User

settings = get_settings()

SAMPLE_CHARITIES = [
    {
        "name": "First Tee Foundation",
        "description": "Helps young people build life skills through golf, funding equipment, coaching, and course access for underserved communities.",
        "website_url": "https://example.org/first-tee",
        "image_url": "https://images.example.org/first-tee.jpg",
        "is_featured": True,
    },
    {
        "name": "Greens for Good",
        "description": "Converts unused urban land into free public putting greens and youth golf clinics.",
        "website_url": "https://example.org/greens-for-good",
        "image_url": "https://images.example.org/greens-for-good.jpg",
        "is_featured": True,
    },
    {
        "name": "Fairway Forward",
        "description": "Provides adaptive golf equipment and coaching for veterans and people with disabilities.",
        "website_url": "https://example.org/fairway-forward",
        "image_url": "https://images.example.org/fairway-forward.jpg",
        "is_featured": False,
    },
]


async def seed():
    if settings.is_sqlite:
        await init_db()

    async with AsyncSessionLocal() as db:
        for data in SAMPLE_CHARITIES:
            existing = await db.execute(select(Charity).where(Charity.name == data["name"]))
            if existing.scalar_one_or_none() is None:
                db.add(Charity(**data))
        await db.commit()

        existing_admin = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        if existing_admin.scalar_one_or_none() is None:
            any_charity = (await db.execute(select(Charity).limit(1))).scalar_one()
            db.add(
                User(
                    username=settings.ADMIN_USERNAME,
                    full_name="Platform Administrator",
                    email=settings.ADMIN_EMAIL,
                    password_hash=hash_password(settings.ADMIN_PASSWORD),
                    role="admin",
                    charity_id=any_charity.id,
                    charity_percentage=10,
                )
            )
            await db.commit()
            if settings.ENVIRONMENT == "production":
                # Never echo the real admin password into production logs.
                print(f"Created admin user '{settings.ADMIN_USERNAME}' - password is the ADMIN_PASSWORD you set.")
            else:
                print(f"Created admin user: {settings.ADMIN_USERNAME} / {settings.ADMIN_PASSWORD}")
        else:
            print("Admin user already exists, skipping.")

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
