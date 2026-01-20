# Docker Setup - Chat Analytics API

Guía completa para ejecutar el proyecto con Docker.

---

## Prerrequisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado
- [Docker Compose](https://docs.docker.com/compose/install/) (incluido en Docker Desktop)
- Archivo `.env` configurado (copiar desde `.env.example`)

---

## Configuración Inicial

### 1. Clonar el repositorio

```bash
git clone <tu-repo-url>
cd chat-analytics-api
```

### 2. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar el archivo .env y configurar:
# - GEMINI_API_KEY (obligatorio)
# - JWT_SECRET (cambiar en producción)
# - Otras variables según necesidad
```

**Variables importantes para Docker:**

```env
# Database (usar 'db' como host en Docker Compose)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/chat_analytics

# JWT
JWT_SECRET=change-this-in-production-to-a-secure-random-string

# Gemini
GEMINI_API_KEY=tu-api-key-de-google-gemini

# CORS (agregar dominios de frontend)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Desarrollo Local con Docker Compose

### Iniciar servicios

```bash
# Construir imágenes y levantar servicios
docker-compose up --build

# O en modo background
docker-compose up -d
```

Esto iniciará:
- **PostgreSQL** en `localhost:5432`
- **FastAPI** en `http://localhost:8000`

### Verificar servicios

```bash
# Ver logs
docker-compose logs -f api

# Ver estado de contenedores
docker-compose ps

# Health check
curl http://localhost:8000/health
```

### Detener servicios

```bash
# Detener contenedores
docker-compose down

# Detener y eliminar volúmenes (base de datos)
docker-compose down -v
```

---

## Comandos Útiles

### Ejecutar comandos dentro del contenedor

```bash
# Entrar al contenedor de la API
docker-compose exec api bash

# Ejecutar migraciones (ejemplo con Alembic)
docker-compose exec api alembic upgrade head

# Ejecutar seeds
docker-compose exec api python -m app.db.seed

# Ejecutar tests
docker-compose exec api pytest
```

### Ver logs

```bash
# Logs de todos los servicios
docker-compose logs -f

# Logs solo de la API
docker-compose logs -f api

# Logs solo de la base de datos
docker-compose logs -f db
```

### Reconstruir imágenes

```bash
# Si cambiaste requirements.txt o el Dockerfile
docker-compose build --no-cache api

# Reconstruir todo desde cero
docker-compose down -v
docker-compose up --build
```

---

## Producción con Docker (sin Compose)

### Build de imagen

```bash
docker build -t chat-analytics-api:latest .
```

### Ejecutar contenedor

```bash
docker run -d \
  --name chat-analytics-api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \
  -e JWT_SECRET="your-secret-key" \
  -e GEMINI_API_KEY="your-api-key" \
  -e CORS_ORIGINS="https://tu-frontend.com" \
  chat-analytics-api:latest
```

---

## Características del Dockerfile

### Multi-stage build
- **Stage 1 (dependencies)**: Instala dependencias con compiladores
- **Stage 2 (runtime)**: Solo runtime, imagen más liviana

### Seguridad
- Usuario no-root (`appuser`)
- Sin cache de pip
- Solo librerías runtime en imagen final

### Optimizaciones
- Cache de layers de Docker para builds rápidos
- Health check integrado
- Hot-reload en desarrollo (via docker-compose)

---

## Deploy en Railway

Railway detecta automáticamente el `Dockerfile` y lo usa para el deploy.

### 1. Crear proyecto en Railway

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Crear proyecto
railway init
```

### 2. Configurar variables de entorno en Railway

En el dashboard de Railway, agregar:

```env
DATABASE_URL=<railway-postgres-connection-string>
JWT_SECRET=<strong-random-string>
GEMINI_API_KEY=<your-api-key>
CORS_ORIGINS=https://tu-frontend.vercel.app
ENVIRONMENT=production
PORT=8000
```

### 3. Deploy

```bash
# Deploy desde CLI
railway up

# O conectar repo de GitHub desde el dashboard
# Railway hará deploy automático en cada push
```

### 4. Agregar base de datos PostgreSQL

- En Railway dashboard, click en "New" → "Database" → "PostgreSQL"
- Railway conectará automáticamente la variable `DATABASE_URL`

---

## Troubleshooting

### Error: "Connection refused" a la base de datos

**Problema**: La API intenta conectarse antes de que PostgreSQL esté listo.

**Solución**: El `docker-compose.yml` ya incluye `depends_on` con health check. Si persiste:

```bash
# Reiniciar servicios
docker-compose restart api
```

### Error: "Port 5432 already in use"

**Problema**: Ya tienes PostgreSQL corriendo localmente.

**Solución**:
```bash
# Opción 1: Detener PostgreSQL local
sudo systemctl stop postgresql  # Linux
brew services stop postgresql   # macOS

# Opción 2: Cambiar puerto en docker-compose.yml
ports:
  - "5433:5432"  # Mapea a 5433 localmente
```

### Error: "GEMINI_API_KEY not found"

**Problema**: Variable de entorno no configurada.

**Solución**:
```bash
# Asegurarse de que .env existe y tiene la variable
echo "GEMINI_API_KEY=tu-key" >> .env

# Reiniciar servicios
docker-compose down && docker-compose up
```

### Limpiar todo y empezar de cero

```bash
# Detener y eliminar contenedores, volúmenes, imágenes
docker-compose down -v --rmi all

# Reconstruir desde cero
docker-compose up --build
```

---

## Referencias

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Railway Documentation](https://docs.railway.app/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
