"""Seed database with sample data for testing."""
import asyncio
from datetime import datetime, timedelta
import random

from app.db.database import async_session_maker, init_db
from app.db.models import User, UserRole, Service, Cost, Expense
from app.auth.service import hash_password


async def seed_database():
    """Seed the database with sample data."""
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
        
        # Create services
        services = [
            Service(name="Cloud Hosting", description="AWS/Azure hosting services", category="Infrastructure"),
            Service(name="SaaS Licenses", description="Software licenses and subscriptions", category="Software"),
            Service(name="Development Team", description="Development and maintenance", category="Human Resources"),
            Service(name="Marketing", description="Digital marketing campaigns", category="Marketing"),
            Service(name="Support", description="Customer support services", category="Operations"),
        ]
        
        for service in services:
            db.add(service)
        
        await db.commit()
        
        # Refresh to get IDs
        for service in services:
            await db.refresh(service)
        
        # Create costs and expenses for each service
        categories = ["Operacional", "Mantenimiento", "Desarrollo", "Licencias", "Personal"]
        
        for service in services:
            # Generate 12 months of data
            for month_offset in range(12):
                date = datetime.now() - timedelta(days=30 * month_offset)
                
                # Random costs (2-5 per month)
                for _ in range(random.randint(2, 5)):
                    cost = Cost(
                        service_id=service.id,
                        amount=round(random.uniform(500, 5000), 2),
                        category=random.choice(categories),
                        description=f"Costo {service.name} - {date.strftime('%B %Y')}",
                        date=date + timedelta(days=random.randint(0, 28)),
                    )
                    db.add(cost)
                
                # Random expenses (2-5 per month)
                for _ in range(random.randint(2, 5)):
                    expense = Expense(
                        service_id=service.id,
                        amount=round(random.uniform(300, 4000), 2),
                        category=random.choice(categories),
                        description=f"Gasto {service.name} - {date.strftime('%B %Y')}",
                        date=date + timedelta(days=random.randint(0, 28)),
                    )
                    db.add(expense)
        
        await db.commit()
        
        print("✅ Database seeded successfully!")
        print("\n📧 Test Users:")
        print("  - admin@example.com / admin123 (Admin)")
        print("  - analyst@example.com / analyst123 (Analyst)")
        print("  - viewer@example.com / viewer123 (Viewer)")
        print(f"\n📦 Created {len(services)} services with costs and expenses")


async def main():
    """Main entry point."""
    await init_db()
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
