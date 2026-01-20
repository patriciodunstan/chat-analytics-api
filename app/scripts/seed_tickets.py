"""Load support tickets from CSV into database."""
import asyncio
import csv
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings
from app.db.models import Base, SupportTicket


async def load_tickets():
    """Load tickets from CSV file."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    csv_path = Path(__file__).parent.parent / "customer_support_tickets.csv"

    async with async_session() as session:
        await session.execute(text("TRUNCATE support_tickets RESTART IDENTITY CASCADE"))
        await session.commit()

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            tickets = []

            for i, row in enumerate(reader):
                try:
                    ticket = SupportTicket(
                        ticket_id=int(row.get('Ticket ID', i+1)),
                        customer_name=row.get('Customer Name'),
                        customer_email=row.get('Customer Email'),
                        customer_age=int(row['Customer Age']) if row.get('Customer Age') else None,
                        customer_gender=row.get('Customer Gender'),
                        product_purchased=row.get('Product Purchased'),
                        date_of_purchase=parse_date(row.get('Date of Purchase')),
                        ticket_type=row.get('Ticket Type'),
                        ticket_subject=row.get('Ticket Subject'),
                        ticket_description=row.get('Ticket Description'),
                        ticket_status=row.get('Ticket Status'),
                        resolution=row.get('Resolution'),
                        ticket_priority=row.get('Ticket Priority'),
                        ticket_channel=row.get('Ticket Channel'),
                        first_response_time=parse_datetime(row.get('First Response Time')),
                        time_to_resolution=parse_datetime(row.get('Time to Resolution')),
                        customer_satisfaction_rating=float(row['Customer Satisfaction Rating']) if row.get('Customer Satisfaction Rating') else None,
                    )
                    tickets.append(ticket)

                    if len(tickets) >= 1000:
                        session.add_all(tickets)
                        await session.commit()
                        print(f"Inserted {i+1} tickets...")
                        tickets = []

                except Exception as e:
                    print(f"Error on row {i}: {e}")
                    continue

            if tickets:
                session.add_all(tickets)
                await session.commit()

        result = await session.execute(text("SELECT COUNT(*) FROM support_tickets"))
        count = result.scalar()
        print(f"\nTotal tickets loaded: {count}")


def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None


def parse_datetime(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None


if __name__ == "__main__":
    asyncio.run(load_tickets())