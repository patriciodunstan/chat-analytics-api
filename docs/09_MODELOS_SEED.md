# 09 - Modelos de Datos y Seeds

## Agregar a `app/db/models.py` (al final del archivo)

```python
# ============================================================
# MODELOS PARA DEMO: MAQUINARIA Y TICKETS
# ============================================================

class Equipment(Base):
    """Equipment/machinery model for maintenance tracking."""
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    tipo_maquina: Mapped[str] = mapped_column(String(50))
    marca: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    modelo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ano: Mapped[Optional[int]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    maintenance_events: Mapped[list["MaintenanceEvent"]] = relationship(
        back_populates="equipment", cascade="all, delete-orphan"
    )
    failure_events: Mapped[list["FailureEvent"]] = relationship(
        back_populates="equipment", cascade="all, delete-orphan"
    )


class MaintenanceEvent(Base):
    """Maintenance event model."""
    __tablename__ = "maintenance_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(String(20), ForeignKey("equipment.equipment_id"))
    fecha: Mapped[datetime] = mapped_column(DateTime)
    tipo_intervencion: Mapped[str] = mapped_column(String(20))
    descripcion_tarea: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    horas_operacion: Mapped[Optional[int]] = mapped_column(nullable=True)
    costo_total: Mapped[Optional[float]] = mapped_column(nullable=True)
    duracion_horas: Mapped[Optional[int]] = mapped_column(nullable=True)
    responsable: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ubicacion_gps: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    equipment: Mapped["Equipment"] = relationship(back_populates="maintenance_events")


class FailureEvent(Base):
    """Failure/breakdown event model."""
    __tablename__ = "failure_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[str] = mapped_column(String(20), ForeignKey("equipment.equipment_id"))
    fecha: Mapped[datetime] = mapped_column(DateTime)
    codigo_falla: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    descripcion_falla: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    causa_raiz: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    horas_operacion: Mapped[Optional[int]] = mapped_column(nullable=True)
    costo_total: Mapped[Optional[float]] = mapped_column(nullable=True)
    duracion_horas: Mapped[Optional[int]] = mapped_column(nullable=True)
    responsable: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ubicacion_gps: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    impacto: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    equipment: Mapped["Equipment"] = relationship(back_populates="failure_events")


class SupportTicket(Base):
    """Customer support ticket model."""
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(unique=True, index=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_age: Mapped[Optional[int]] = mapped_column(nullable=True)
    customer_gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    product_purchased: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date_of_purchase: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ticket_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ticket_subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ticket_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ticket_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ticket_priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ticket_channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    first_response_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    time_to_resolution: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    customer_satisfaction_rating: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

---

## Archivo: `scripts/seed_equipment.sql`

```sql
-- SEED DE EQUIPOS Y EVENTOS DE MANTENIMIENTO
-- Ejecutar: psql -U usuario -d basedatos -f scripts/seed_equipment.sql

-- Limpiar tablas existentes
TRUNCATE failure_events, maintenance_events, equipment RESTART IDENTITY CASCADE;

-- INSERT DE EQUIPOS (50 equipos)
INSERT INTO equipment (equipment_id, tipo_maquina, marca, modelo, ano)
SELECT
    'EQ-' || lpad(gs::text, 3, '0'),
    (ARRAY['Excavadora','Cargador','Motoniveladora','Compactador','Dump Truck','Retroexcavadora'])[floor(random()*6)+1],
    (ARRAY['Caterpillar','Komatsu','Volvo','John Deere','Hyundai','Doosan','BOMAG','JCB'])[floor(random()*8)+1],
    'MD-' || floor(random()*500 + 100),
    floor(random()*10 + 2015)
FROM generate_series(1,50) gs;

-- INSERT DE MANTENIMIENTOS (5,000 registros)
INSERT INTO maintenance_events (
    equipment_id, fecha, tipo_intervencion, descripcion_tarea,
    horas_operacion, costo_total, duracion_horas, responsable, ubicacion_gps
)
SELECT
    'EQ-' || lpad((floor(random()*50)+1)::text,3,'0'),
    date '2022-01-01' + (floor(random()*800)) * interval '1 day',
    (ARRAY['Preventivo','Preventivo','Preventivo','Predictivo'])[floor(random()*4)+1],
    (ARRAY['Cambio aceite y filtros','Revisión general','Lubricación articulaciones',
           'Ajuste frenos','Inspección hidráulica','Análisis de vibraciones'])[floor(random()*6)+1],
    floor(random()*9000 + 500),
    floor(random()*1500000 + 50000),
    floor(random()*6 + 1),
    (ARRAY['Técnico A','Técnico B','Técnico C','Técnico D','Sistema IoT'])[floor(random()*5)+1],
    '-33.' || floor(random()*600) || ',-70.' || floor(random()*700)
FROM generate_series(1,5000);

-- INSERT DE FALLAS (3,000 registros)
INSERT INTO failure_events (
    equipment_id, fecha, codigo_falla, descripcion_falla, causa_raiz,
    horas_operacion, costo_total, duracion_horas, responsable, ubicacion_gps, impacto
)
SELECT
    'EQ-' || lpad((floor(random()*50)+1)::text,3,'0'),
    date '2022-01-01' + (floor(random()*800)) * interval '1 day',
    'F-' || floor(random()*999 + 1),
    (ARRAY['Baja presión aceite','Vibración anormal','Freno sin accionamiento',
           'Sobrecalentamiento motor','Fuga hidráulica','Dificultad encendido'])[floor(random()*6)+1],
    (ARRAY['Desgaste por uso','Falta de lubricación','Sensor fallado',
           'Obstrucción radiador','Rotura de sello','Fatiga mecánica'])[floor(random()*6)+1],
    floor(random()*9000 + 500),
    floor(random()*2000000 + 100000),
    floor(random()*10 + 1),
    (ARRAY['Técnico A','Técnico B','Técnico C','Técnico D'])[floor(random()*4)+1],
    '-33.' || floor(random()*600) || ',-70.' || floor(random()*700),
    (ARRAY['Detención 2h','Detención 4h','Detención 6h','Detención 8h','Detención 1h'])[floor(random()*5)+1]
FROM generate_series(1,3000);

-- Verificar
SELECT 'equipment' as tabla, COUNT(*) as registros FROM equipment
UNION ALL SELECT 'maintenance_events', COUNT(*) FROM maintenance_events
UNION ALL SELECT 'failure_events', COUNT(*) FROM failure_events;
```

---

## Archivo: `scripts/seed_tickets.py`

```python
"""Load support tickets from CSV into database."""
import asyncio
import csv
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.config import settings
from app.db.models import SupportTicket, Base


async def load_tickets():
    """Load tickets from CSV file."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

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
```

---

## Comandos para ejecutar seeds

```bash
# 1. Crear tablas (reiniciar app o ejecutar)
uvicorn app.main:app --reload

# 2. Ejecutar seed de equipos
psql -U tu_usuario -d tu_base -f scripts/seed_equipment.sql

# 3. Ejecutar seed de tickets
python scripts/seed_tickets.py
```
