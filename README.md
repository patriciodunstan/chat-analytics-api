# Chat Analytics API

[![Deploy](https://github.com/patriciodunstan/chat-analytics-api/actions/workflows/deploy.yml/badge.svg)](https://github.com/patriciodunstan/chat-analytics-api/actions/workflows/deploy.yml)
[![CI](https://github.com/patriciodunstan/chat-analytics-api/actions/workflows/ci.yml/badge.svg)](https://github.com/patriciodunstan/chat-analytics-api/actions/workflows/ci.yml)

Backend FastAPI para consultas de datos en lenguaje natural con LLM. POC de sistema NL2SQL genérico que se adapta a cualquier base de datos PostgreSQL mediante auto-descubrimiento de esquema.

---

## Características

- **NL2SQL**: Consultas en español sobre cualquier base de datos
- **Auto-descubrimiento**: Detecta automáticamente el esquema de la DB
- **Chat con LLM**: Integración con Google Gemini
- **Reportes PDF**: Generación automática con gráficos
- **Autenticación JWT**: Roles (VIEWER, ANALYST, ADMIN)
- **API RESTful**: Documentación automática con Swagger/OpenAPI
- **CI/CD**: GitHub Actions con tests automáticos y deploy a Railway

---

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Framework** | FastAPI 0.109+ |
| **Base de datos** | PostgreSQL 15+ |
| **ORM** | SQLAlchemy 2.0 (async) |
| **LLM** | Google Gemini 1.5 Flash |
| **Auth** | JWT + bcrypt |
| **Reportes** | ReportLab + matplotlib |
| **Testing** | pytest + pytest-asyncio |
| **Contenedores** | Docker + Docker Compose |

---

## Inicio Rápido

### Opción 1: Con Docker (Recomendado)

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd chat-analytics-api

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar GEMINI_API_KEY

# 3. Levantar servicios
docker-compose up --build

# 4. Acceder a la API
open http://localhost:8000/docs
```

Ver guía completa: [DOCKER.md](DOCKER.md)

### Opción 2: Sin Docker

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar PostgreSQL local
createdb chat_analytics

# 4. Configurar .env
cp .env.example .env
# Editar DATABASE_URL y GEMINI_API_KEY

# 5. Ejecutar migraciones (si usas Alembic)
alembic upgrade head

# 6. Iniciar servidor
uvicorn app.main:app --reload

# 7. Acceder a la API
open http://localhost:8000/docs
```

---

## Estructura del Proyecto

```
chat-analytics-api/
├── app/
│   ├── auth/              # Autenticación JWT + roles
│   ├── chat/
│   │   ├── nl2sql/        # Motor NL2SQL (detector, parser, generator, executor)
│   │   └── llm/           # Cliente Google Gemini
│   ├── reports/           # Generación de reportes PDF
│   ├── db/                # SQLAlchemy modelos y base de datos
│   ├── config.py          # Configuración centralizada
│   └── main.py            # Aplicación FastAPI
├── tests/                 # Tests unitarios e integración
├── scripts/               # Seeds y scripts de utilidad
├── docs/                  # Documentación adicional
├── Dockerfile             # Imagen Docker producción
├── docker-compose.yml     # Orquestación servicios (dev)
├── requirements.txt       # Dependencias Python
└── .env.example           # Plantilla de variables de entorno
```

---

## Datasets de Demostración

### Dataset 1: Minería
- `equipment`: Equipos industriales
- `maintenance_events`: Eventos de mantenimiento
- `failure_events`: Fallos y averías

### Dataset 2: Soporte Técnico
- `support_tickets`: ~8,000 tickets de soporte

**Cargar seeds:**
```bash
# Con Docker
docker-compose exec api python -m app.db.seed
docker-compose exec api python app/scripts/seed_tickets.py

# Sin Docker
python -m app.db.seed
python app/scripts/seed_tickets.py

# En Railway
railway run python -m app.db.seed
railway run python app/scripts/seed_tickets.py
```

Ver guía completa: [SEEDS_RAILWAY.md](SEEDS_RAILWAY.md)

---

## Documentación

- **[Setup Guide](SETUP.md)**: Guía rápida de instalación y deploy
- **[Seeds Railway](SEEDS_RAILWAY.md)**: Cómo cargar datos en Railway
- **[API Reference](docs/API.md)**: Endpoints completos para integración frontend
- **[Docker Guide](DOCKER.md)**: Setup con contenedores
- **[Railway Deployment](RAILWAY.md)**: Deploy en producción
- **Swagger UI**: http://localhost:8000/docs - Documentación interactiva

---

## Endpoints Principales

### Autenticación
- `POST /auth/register` - Registrar usuario
- `POST /auth/login` - Login (obtener token)
- `GET /auth/me` - Usuario actual

### Chat
- `POST /chat/message` - Enviar mensaje al LLM
- `GET /chat/conversations` - Listar conversaciones
- `GET /chat/conversations/{id}` - Obtener conversación

### Reportes (requiere rol ANALYST/ADMIN)
- `POST /reports/generate` - Generar reporte PDF
- `GET /reports/list` - Listar reportes
- `GET /reports/{id}/download` - Descargar PDF

Ver documentación completa: [docs/API.md](docs/API.md)

---

## Tests

```bash
# Con Docker
docker-compose exec api pytest

# Sin Docker
pytest

# Con cobertura
pytest --cov=app tests/

# Tests específicos
pytest tests/test_auth.py -v
pytest tests/test_nl2sql.py -v
```

---

## Deployment

### Railway (Recomendado)

```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login y crear proyecto
railway login
railway init

# 3. Agregar PostgreSQL desde dashboard
# 4. Configurar variables de entorno
# 5. Deploy
railway up
```

Ver guía completa: [RAILWAY.md](RAILWAY.md)

### Render, Heroku, etc.

El proyecto incluye `Dockerfile` y puede deployarse en cualquier plataforma que soporte contenedores.

---

## Variables de Entorno

```env
# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# JWT
JWT_SECRET=change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Google Gemini (gratis: https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-1.5-flash

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Roles y Permisos

| Rol | Permisos |
|-----|----------|
| **VIEWER** | Chat, ver servicios, ver reportes propios |
| **ANALYST** | Todo de VIEWER + crear servicios/costos + generar reportes |
| **ADMIN** | Todos los permisos |

---

## Flujo NL2SQL

```
Usuario: "¿Cuántos equipos fallaron en enero?"
    ↓
[Detector] ¿Es query? → SÍ
    ↓
[Schema Discovery] → Obtiene esquema de tablas
    ↓
[Intent Parser] → Identifica intención y entidades
    ↓
[SQL Generator] → Genera SQL seguro
    ↓
[Query Executor] → Ejecuta en DB
    ↓
[LLM] → Responde en lenguaje natural con resultados
    ↓
Usuario: "En enero fallaron 15 equipos, principalmente..."
```

---

## Contribuir

1. Fork del repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'feat: add nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

### Convenciones de Commits

Formato: `tipo(scope): descripción`

Tipos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Ejemplos:
- `feat(auth): add refresh token support`
- `fix(nl2sql): handle null values in queries`
- `docs(api): update endpoint documentation`

---

## Troubleshooting

### Error: "GEMINI_API_KEY not found"

**Solución**: Configurar API key en `.env`:
```bash
GEMINI_API_KEY=tu-api-key
```

Obtener gratis en: https://makersuite.google.com/app/apikey

### Error: "Connection refused" a PostgreSQL

**Solución con Docker**:
```bash
docker-compose down
docker-compose up -d
```

**Solución sin Docker**: Verificar que PostgreSQL esté corriendo:
```bash
# Linux
sudo systemctl start postgresql

# macOS
brew services start postgresql
```

### Error: "Could not validate credentials"

**Solución**: Token expirado. Hacer login nuevamente:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}'
```

---

## Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

---

## Contacto y Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/chat-analytics-api/issues)
- **Documentación**: Ver carpeta `docs/`
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

---

## Roadmap

- [ ] Soporte para múltiples LLMs (OpenAI, Claude, local)
- [ ] Cache de queries frecuentes
- [ ] Streaming de respuestas
- [ ] Dashboard de analytics
- [ ] Integración con más bases de datos (MySQL, MongoDB)
- [ ] Fine-tuning del modelo para dominio específico
