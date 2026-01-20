"""Seed database with sample data for testing."""
import asyncio

from app.db.database import async_session_maker, init_db
from app.db.models import User, UserRole
from app.auth.service import hash_password


async def seed_database():
    """Seed the database with sample users."""
    async with async_session_maker() as db:
        # Create users
        users = [
            User(
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                full_name="Admin User",
                role=UserRole.ADMIN,
            ),
            User(
                email="analyst@example.com",
                password_hash=hash_password("analyst123"),
                full_name="Analyst User",
                role=UserRole.ANALYST,
            ),
            User(
                email="viewer@example.com",
                password_hash=hash_password("viewer123"),
                full_name="Viewer User",
                role=UserRole.VIEWER,
            ),
        ]

        for user in users:
            db.add(user)

        await db.commit()

        print("✅ Database seeded successfully!")
        print("\n📧 Test Users:")
        print("  - admin@example.com / admin123 (Admin)")
        print("  - analyst@example.com / analyst123 (Analyst)")
        print("  - viewer@example.com / viewer123 (Viewer)")
        print("\n📝 Para cargar datos de demostración:")
        print("  - Minería: psql -U user -d db -f scripts/seed_equipment.sql")
        print("  - Soporte: python scripts/seed_tickets.py")


async def main():
    """Main entry point."""
    await init_db()
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())