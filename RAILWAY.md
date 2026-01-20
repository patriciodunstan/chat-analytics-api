# Railway Deployment Guide

Guía paso a paso para deployar Chat Analytics API en Railway.

---

## Prerrequisitos

- Cuenta en [Railway](https://railway.app)
- Repositorio Git (GitHub, GitLab o Bitbucket)
- API Key de Google Gemini

---

## Opción 1: Deploy desde Dashboard (Recomendado)

### 1. Crear Proyecto

1. Ir a [railway.app](https://railway.app) y hacer login
2. Click en "New Project"
3. Seleccionar "Deploy from GitHub repo"
4. Autorizar Railway a acceder a tu repositorio
5. Seleccionar el repositorio `chat-analytics-api`

### 2. Agregar PostgreSQL

1. En el proyecto, click en "New" → "Database" → "Add PostgreSQL"
2. Railway creará automáticamente:
   - Base de datos PostgreSQL
   - Variable de entorno `DATABASE_URL`

### 3. Configurar Variables de Entorno

En el servicio de la API, ir a "Variables" y agregar:

```env
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database (ya está configurada automáticamente)
# DATABASE_URL=<auto-configurada-por-railway>

# JWT (generar string aleatorio seguro)
JWT_SECRET=<generar-con: openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Google Gemini
GEMINI_API_KEY=<tu-api-key>
GEMINI_MODEL=gemini-2.0-flash-exp

# CORS (agregar dominio de frontend)
CORS_ORIGINS=https://tu-frontend.vercel.app,https://tu-dominio.com

# Puerto (Railway lo configura automáticamente)
PORT=${{PORT}}
```

### 4. Deploy

Railway detectará el `Dockerfile` y comenzará el deploy automáticamente.

- **Build**: ~3-5 minutos (primera vez)
- **Health check**: Railway esperará a que `/health` responda 200

### 5. Obtener URL del Servicio

1. En el dashboard, click en tu servicio
2. Ir a "Settings" → "Networking"
3. Click en "Generate Domain"
4. Railway generará una URL como: `https://tu-proyecto.up.railway.app`

### 6. Ejecutar Migraciones (Si usas Alembic)

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Conectar al proyecto
railway link

# Ejecutar migraciones
railway run alembic upgrade head
```

---

## Opción 2: Deploy desde Railway CLI

### 1. Instalar Railway CLI

```bash
npm install -g @railway/cli
```

### 2. Login y Setup

```bash
# Login
railway login

# Crear nuevo proyecto
railway init

# Vincular a proyecto existente
railway link
```

### 3. Agregar PostgreSQL

```bash
# En el dashboard de Railway
# New → Database → PostgreSQL
```

### 4. Configurar Variables

```bash
# Configurar variables de entorno
railway variables set JWT_SECRET=$(openssl rand -hex 32)
railway variables set GEMINI_API_KEY="tu-api-key"
railway variables set CORS_ORIGINS="https://tu-frontend.com"
railway variables set ENVIRONMENT="production"
```

### 5. Deploy

```bash
# Deploy
railway up

# Ver logs
railway logs
```

---

## Configuración de Base de Datos

### Verificar Conexión

```bash
# Ver variables de entorno
railway variables

# Ejecutar comando en el servicio
railway run python -c "from app.db.database import engine; print('DB OK')"
```

### Ejecutar Seeds (Opcional)

```bash
# Seed de usuarios de prueba
railway run python -m app.db.seed

# Seed de equipos (mining domain)
railway run psql $DATABASE_URL -f app/scripts/seed_equipment.sql

# Seed de tickets (support domain)
railway run python app/scripts/seed_tickets.py
```

**Ver guía completa**: [SEEDS_RAILWAY.md](SEEDS_RAILWAY.md)

---

## Monitoreo y Mantenimiento

### Ver Logs

```bash
# Desde CLI
railway logs

# O desde el dashboard:
# Proyecto → Servicio → Logs
```

### Métricas

En el dashboard de Railway:
- **CPU Usage**
- **Memory Usage**
- **Network**
- **Response Times**

### Reiniciar Servicio

```bash
# Desde CLI
railway restart

# O desde el dashboard:
# Settings → Restart
```

---

## Configuración Avanzada

### Custom Domain

1. En el dashboard: Settings → Networking → Custom Domain
2. Agregar tu dominio (ej: `api.tuempresa.com`)
3. Configurar registro CNAME en tu proveedor DNS:
   ```
   CNAME api -> tu-proyecto.up.railway.app
   ```

### Health Checks

Railway usa el endpoint `/health` automáticamente. Configuración en [railway.json](railway.json):

```json
{
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300
  }
}
```

### Escalamiento

Railway escala automáticamente. Configurar límites:

1. Settings → Resources
2. Ajustar:
   - **Memory**: 512MB - 8GB
   - **CPU**: 1-8 vCPUs

---

## Costos Estimados (Railway)

| Plan | Precio | Recursos |
|------|--------|----------|
| **Trial** | $0 | $5 crédito inicial (500 horas) |
| **Developer** | $5/mes | $5 crédito + extras |
| **Pro** | Variable | Pay-as-you-go |

**Estimación para este proyecto:**
- API + PostgreSQL: ~$5-10/mes (uso moderado)
- Base de datos < 1GB
- Tráfico < 100GB/mes

[Más info sobre pricing](https://railway.app/pricing)

---

## Troubleshooting

### Error: "Application failed to respond"

**Causa**: La app no responde en el puerto correcto.

**Solución**: Verificar que `app/main.py` use `0.0.0.0`:
```python
# Ya está configurado en config.py
api_host: str = "0.0.0.0"
```

### Error: "Database connection failed"

**Causa**: Variable `DATABASE_URL` no está configurada.

**Solución**:
```bash
# Verificar que PostgreSQL esté agregado al proyecto
railway variables | grep DATABASE_URL

# Si no existe, agregar base de datos desde el dashboard
```

### Error: "Health check timeout"

**Causa**: La app tarda mucho en iniciar.

**Solución**: Aumentar timeout en `railway.json`:
```json
{
  "deploy": {
    "healthcheckTimeout": 600
  }
}
```

### Error: "Module not found"

**Causa**: Dependencias no instaladas correctamente.

**Solución**: Verificar `requirements.txt` y rebuild:
```bash
# Forzar rebuild
railway up --detach
```

---

## Migrar de Render a Railway

Si ya tienes el proyecto en Render:

### 1. Exportar Variables de Entorno

Desde Render dashboard, copiar todas las variables.

### 2. Backup de Base de Datos

```bash
# Dump de Render DB
pg_dump $RENDER_DATABASE_URL > backup.sql

# Restaurar en Railway DB
railway run psql $DATABASE_URL < backup.sql
```

### 3. Configurar Railway

Seguir pasos de "Opción 1" arriba.

### 4. Actualizar Frontend

Cambiar URL de API en tu frontend de:
```
https://tu-app.onrender.com
```
a:
```
https://tu-app.up.railway.app
```

---

## Automatización CI/CD

Railway hace deploy automático en cada push a `main`. Para configurar:

1. Settings → Service → Deploy Triggers
2. Seleccionar rama: `main` (ya no `master`)
3. Railway hará deploy automático en cada commit

### GitHub Actions (Opcional)

Si quieres más control:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --detach
```

---

## Referencias

- [Railway Documentation](https://docs.railway.app/)
- [Railway CLI Reference](https://docs.railway.app/develop/cli)
- [Railway Deployment Guide](https://docs.railway.app/deploy/deployments)
- [PostgreSQL en Railway](https://docs.railway.app/databases/postgresql)
