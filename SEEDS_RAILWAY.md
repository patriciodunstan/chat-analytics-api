# Cargar Seeds en Railway

Guía para poblar la base de datos PostgreSQL en Railway con datos de demostración.

---

## Opción 1: Railway CLI (Recomendada)

### 1. Instalar Railway CLI

```bash
npm install -g @railway/cli
```

### 2. Login y conectar al proyecto

```bash
railway login
railway link  # Seleccionar tu proyecto
```

### 3. Cargar seeds de usuarios

Este comando crea 3 usuarios de prueba (admin, analyst, viewer):

```bash
railway run python -m app.db.seed
```

**Usuarios creados:**
- `admin@example.com` / `admin123` (Admin)
- `analyst@example.com` / `analyst123` (Analyst)
- `viewer@example.com` / `viewer123` (Viewer)

### 4. Cargar datos de Mining Domain (Equipos)

```bash
# Opción A: Ejecutar script SQL directamente
railway run psql $DATABASE_URL -f app/scripts/seed_equipment.sql

# Opción B: Si el script está en otra ubicación
cat app/scripts/seed_equipment.sql | railway run psql $DATABASE_URL
```

Esto carga datos de:
- `equipment` (equipos industriales)
- `maintenance_events` (mantenimiento)
- `failure_events` (fallos)

### 5. Cargar datos de Support Domain (Tickets)

```bash
railway run python app/scripts/seed_tickets.py
```

Esto carga ~8,000 tickets de soporte técnico en `support_tickets`.

---

## Opción 2: Desde la Aplicación Deployada

### Crear endpoint temporal de seed

Agregar a `app/main.py`:

```python
from app.db.seed import seed_database

@app.post("/admin/seed", tags=["Admin"])
async def seed_db_endpoint():
    """Seed database (use only once, remove after)."""
    await seed_database()
    return {"message": "Database seeded successfully"}
```

Luego:

```bash
# Hacer request POST al endpoint
curl -X POST https://tu-app.up.railway.app/admin/seed

# IMPORTANTE: Eliminar el endpoint después de usar
```

---

## Opción 3: Conectarse Directamente a PostgreSQL

### 1. Obtener credenciales

En Railway dashboard → PostgreSQL → Connect → Connection URL

```
postgresql://user:password@host:port/database
```

### 2. Conectar con psql local

```bash
psql "postgresql://user:password@host:port/database"
```

### 3. Ejecutar scripts SQL

```sql
-- Desde psql
\i app/scripts/seed_equipment.sql

-- O desde bash
psql "postgresql://..." -f app/scripts/seed_equipment.sql
```

### 4. Ejecutar seeds Python

```bash
# Configurar DATABASE_URL local apuntando a Railway
export DATABASE_URL="postgresql+asyncpg://user:password@host:port/database"

# Ejecutar seeds
python -m app.db.seed
python app/scripts/seed_tickets.py
```

---

## Opción 4: Automático en Deploy

### Modificar `railway.json`

Para que los seeds se ejecuten automáticamente en cada deploy:

```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "python -m app.db.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300
  }
}
```

⚠️ **Advertencia**: Esto ejecutará seeds en cada deploy. Solo usar para desarrollo.

Para producción, mejor usar migraciones con flags:

```python
# En seed.py
import os

async def seed_database():
    if os.getenv("RUN_SEEDS") != "true":
        print("Skipping seeds (RUN_SEEDS not set)")
        return

    # ... seed logic
```

Luego en Railway, agregar variable de entorno temporal:
```
RUN_SEEDS=true  # Solo cuando quieras ejecutar seeds
```

---

## Verificar que los Seeds se Cargaron

### Opción A: Railway CLI

```bash
# Ver usuarios
railway run python -c "
from app.db.database import async_session_maker
from app.db.models import User
import asyncio

async def check():
    async with async_session_maker() as db:
        from sqlalchemy import select
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f'Users: {len(users)}')
        for u in users:
            print(f'  - {u.email} ({u.role})')

asyncio.run(check())
"

# Contar equipos
railway run python -c "
from app.db.database import async_session_maker
from app.db.models import Equipment
import asyncio

async def check():
    async with async_session_maker() as db:
        from sqlalchemy import select, func
        result = await db.execute(select(func.count()).select_from(Equipment))
        count = result.scalar()
        print(f'Equipment records: {count}')

asyncio.run(check())
"
```

### Opción B: psql

```bash
railway run psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
railway run psql $DATABASE_URL -c "SELECT COUNT(*) FROM equipment;"
railway run psql $DATABASE_URL -c "SELECT COUNT(*) FROM support_tickets;"
```

### Opción C: Desde la API

```bash
# Login
curl -X POST https://tu-app.up.railway.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Debería retornar token si el seed funcionó
```

---

## Scripts de Seed Disponibles

| Script | Descripción | Comando |
|--------|-------------|---------|
| `app/db/seed.py` | Usuarios de prueba (admin, analyst, viewer) | `python -m app.db.seed` |
| `app/scripts/seed_equipment.sql` | Equipos industriales + mantenimiento + fallos | `psql $DATABASE_URL -f app/scripts/seed_equipment.sql` |
| `app/scripts/seed_tickets.py` | ~8,000 tickets de soporte técnico | `python app/scripts/seed_tickets.py` |

---

## Ejemplo Completo: Seed Todo en Railway

```bash
# 1. Setup Railway CLI
npm install -g @railway/cli
railway login
railway link

# 2. Seed usuarios
railway run python -m app.db.seed

# 3. Seed equipos (mining domain)
railway run psql $DATABASE_URL -f app/scripts/seed_equipment.sql

# 4. Seed tickets (support domain)
railway run python app/scripts/seed_tickets.py

# 5. Verificar
railway run psql $DATABASE_URL -c "
SELECT
  'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'equipment', COUNT(*) FROM equipment
UNION ALL
SELECT 'maintenance_events', COUNT(*) FROM maintenance_events
UNION ALL
SELECT 'failure_events', COUNT(*) FROM failure_events
UNION ALL
SELECT 'support_tickets', COUNT(*) FROM support_tickets;
"
```

Salida esperada:
```
      table_name      | count
----------------------+-------
 users                |     3
 equipment            |    50
 maintenance_events   |   150
 failure_events       |    75
 support_tickets      |  8000
```

---

## Troubleshooting

### Error: "psql: command not found"

**Solución**: Instalar PostgreSQL client local:

```bash
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt-get install postgresql-client

# Windows
# Descargar desde: https://www.postgresql.org/download/windows/
```

### Error: "ModuleNotFoundError" al ejecutar seeds

**Causa**: Dependencias de Python no instaladas en el servicio.

**Solución**: Los seeds se deben ejecutar desde un contenedor que tenga las dependencias:

```bash
# Railway ejecuta dentro del contenedor
railway run python -m app.db.seed  # ✅ Correcto

# Esto NO funcionará si lo ejecutas local apuntando a Railway DB
python -m app.db.seed  # ❌ Falta DATABASE_URL o dependencias
```

### Error: "relation 'users' does not exist"

**Causa**: Tablas no creadas (falta ejecutar migraciones o init_db).

**Solución**:

```bash
# La app debería crear las tablas al iniciar (init_db en lifespan)
# Si no, ejecutar manualmente:
railway run python -c "
from app.db.database import init_db
import asyncio
asyncio.run(init_db())
"
```

O verificar que la app se haya iniciado al menos una vez (el lifespan crea las tablas).

### Seeds se ejecutan múltiples veces

**Problema**: Los usuarios duplicados causan errores.

**Solución**: Agregar verificación en `seed.py`:

```python
from sqlalchemy import select

async def seed_database():
    async with async_session_maker() as db:
        # Verificar si ya hay usuarios
        result = await db.execute(select(User))
        if result.scalars().first():
            print("⚠️  Database already seeded, skipping...")
            return

        # ... resto del código de seed
```

---

## Resumen: Método Recomendado

```bash
# Una sola vez, después del primer deploy:
railway login
railway link
railway run python -m app.db.seed
railway run psql $DATABASE_URL -f app/scripts/seed_equipment.sql
railway run python app/scripts/seed_tickets.py
```

¡Listo! 🎉 Tu base de datos en Railway tendrá todos los datos de demostración.

---

## Referencias

- [Railway CLI Docs](https://docs.railway.app/develop/cli)
- [Railway Database Docs](https://docs.railway.app/databases/postgresql)
- [SETUP.md](SETUP.md) - Guía de instalación local
