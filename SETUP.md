# Setup Guide - Chat Analytics API

Guía rápida para poner en marcha el proyecto.

---

## Inicio Rápido con Docker (Recomendado)

```bash
# 1. Clonar y configurar
git clone <repo-url>
cd chat-analytics-api
cp .env.example .env

# 2. Editar .env y agregar GEMINI_API_KEY
# Obtener key gratis en: https://makersuite.google.com/app/apikey

# 3. Leventar servicios
docker-compose up --build

# 4. Acceder
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

## Sin Docker

```bash
# 1. Entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Dependencias
pip install -r requirements.txt

# 3. PostgreSQL
createdb chat_analytics

# 4. Variables de entorno
cp .env.example .env
# Editar DATABASE_URL y GEMINI_API_KEY

# 5. Servidor
uvicorn app.main:app --reload
```

---

## Deploy en Railway

```bash
# Opción A: Desde Dashboard (más fácil)
# 1. Conectar repo de GitHub en railway.app
# 2. Agregar PostgreSQL desde dashboard
# 3. Configurar variables de entorno (ver abajo)
# 4. Deploy automático

# Opción B: Desde CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

### Variables de entorno en Railway

```env
JWT_SECRET=<generar con: openssl rand -hex 32>
GEMINI_API_KEY=<tu-api-key>
CORS_ORIGINS=https://tu-frontend.vercel.app
ENVIRONMENT=production
```

> DATABASE_URL se configura automáticamente al agregar PostgreSQL

---

## Comandos Útiles

### Docker

```bash
# Logs
docker-compose logs -f api

# Tests
docker-compose exec api pytest

# Seeds
docker-compose exec api python -m app.db.seed

# Bash
docker-compose exec api bash

# Detener
docker-compose down
```

### Railway

```bash
railway logs              # Ver logs
railway variables         # Ver variables
railway run <command>     # Ejecutar comando
```

### Git

Rama principal es ahora `main` (no `master`):

```bash
git push -u origin main  # Primera vez
```

---

## Documentación

- [README.md](README.md) - Overview del proyecto
- [docs/API.md](docs/API.md) - Referencia completa de la API
- [DOCKER.md](DOCKER.md) - Guía detallada de Docker
- [RAILWAY.md](RAILWAY.md) - Guía detallada de Railway
- Swagger: http://localhost:8000/docs

---

## Troubleshooting

### Error: "GEMINI_API_KEY not found"

```bash
# Agregar a .env
echo "GEMINI_API_KEY=tu-key" >> .env
docker-compose restart api
```

### Error: "Connection refused" a PostgreSQL

```bash
# Con Docker
docker-compose restart api

# Sin Docker: verificar que PostgreSQL esté corriendo
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS
```

### Swagger retorna 404 en un endpoint

Verificar en [docs/API.md](docs/API.md) si el endpoint existe realmente.

Solo están implementados: `/auth`, `/chat`, `/reports`, `/health`

---

## Próximos Pasos

1. Probar localmente con Docker
2. Revisar Swagger: http://localhost:8000/docs
3. Hacer commit y push a `main`
4. Deployar en Railway
5. Conectar frontend

¡Listo para usar! 🚀
