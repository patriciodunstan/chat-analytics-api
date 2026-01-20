# CLAUDE.md

Este archivo proporciona guía a Claude Code para trabajar con este repositorio.

---

## Principios de Desarrollo

### Metodología
- **Arquitectura Limpia**: Separación clara de capas (domain, application, infrastructure)
- **Código Limpio**: Nombres descriptivos, funciones pequeñas, responsabilidad única
- **KISS**: Soluciones simples antes que complejas
- **SOLID**: Single responsibility, Open/closed, Liskov, Interface segregation, Dependency inversion
- **DRY**: No repetir código, abstraer patrones comunes

### Proceso de Desarrollo
1. **Entender necesidades** antes de proponer soluciones
2. **Plan inicial** con historias de usuario antes de codificar
3. **Elegir tecnología adecuada** al problema, no al revés
4. **Iteración incremental** con entregables pequeños y funcionales

### Comunicación
- Usar lenguaje técnico de informática
- Explicar decisiones arquitectónicas con justificación
- Documentar trade-offs cuando existan alternativas

---

## Stack Tecnológico Preferido

| Capa | Tecnologías |
|------|-------------|
| **Backend** | Python + FastAPI (principal), Node.js + NestJS (alternativa) |
| **Frontend** | React (principal), Angular (alternativa) |
| **Base de datos** | PostgreSQL (relacional), MongoDB (NoSQL según caso) |
| **ORM/ODM** | SQLAlchemy (Python), Prisma/TypeORM (Node) |
| **Cloud** | Railway, Azure, AWS |
| **Contenedores** | Docker, Docker Compose |

---

## Project Overview

**POC de NL2SQL Genérico** - Backend FastAPI para consultas de datos en lenguaje natural. Se adapta a cualquier base de datos PostgreSQL mediante auto-descubrimiento de esquema.

### Características principales
- **NL2SQL**: Consultas en español sobre cualquier base de datos
- **Auto-descubrimiento**: Detecta automáticamente el esquema de la DB
- **Chat con LLM**: Integración con Google Gemini
- **Reportes PDF**: Generación automática
- **Auth JWT**: Roles (VIEWER, ANALYST, ADMIN)

### Datasets de Demostración
- **Minería**: equipment, maintenance_events, failure_events
- **Soporte**: support_tickets (~8,000 registros)

---

## Comandos Comunes

```bash
# Instalar dependencias
pip install -r requirements.txt

# Servidor de desarrollo
uvicorn app.main:app --reload

# Tests
pytest
pytest tests/test_auth.py -v

# Seeds de datos
python -m app.db.seed
psql -U user -d db -f scripts/seed_equipment.sql
python scripts/seed_tickets.py
```

---

## Arquitectura

### Estructura de Módulos

```
app/
├── auth/              # JWT + bcrypt, roles: VIEWER, ANALYST, ADMIN
├── chat/
│   ├── nl2sql/         # NL2SQL: detector, parser, generator, executor
│   └── llm/            # Cliente Gemini
├── reports/           # Generación PDF con ReportLab + matplotlib
├── db/                # SQLAlchemy async, modelos
├── config.py          # Settings
└── main.py            # FastAPI app
```

### Patrones Clave

| Patrón | Implementación |
|--------|----------------|
| **Service Layer** | `service.py` en cada módulo con lógica de negocio |
| **Dependency Injection** | `Depends()` de FastAPI para DB y auth |
| **Singleton** | `gemini_client` instancia global |

### Flujo NL2SQL

```
Usuario pregunta → Detector (¿es query?) → Schema Discovery
→ Intent Parser → SQL Generator → Query Executor → Respuesta LLM
```

### Modelos de Datos

```
# Auth & Chat
User → Conversation → Message
User → Report

# Minería (Dataset 1)
Equipment → MaintenanceEvent, FailureEvent

# Soporte (Dataset 2)
SupportTicket
```

---

## Testing

- **DB**: SQLite in-memory para tests
- **LLM**: Mock de `gemini_client`
- **Fixtures**: `client`, `test_user`, `auth_headers` en `conftest.py`

```bash
# Tests NL2SQL
pytest tests/test_nl2sql.py -v

# Tests chat
pytest tests/test_chat.py -v
```

---

## Variables de Entorno

```env
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Auth
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# LLM
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-1.5-flash

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Planificación de Features

### Formato de Historia de Usuario

```
Como [rol]
Quiero [acción]
Para [beneficio]

Criterios de aceptación:
- [ ] Criterio 1
- [ ] Criterio 2

Tareas técnicas:
- [ ] Tarea 1
- [ ] Tarea 2
```

### Ejemplo

```
Como analista
Quiero hacer preguntas en español sobre mis datos
Para obtener insights sin conocer SQL

Criterios de aceptación:
- [ ] Detecta si el mensaje requiere consultar datos
- [ ] Genera SQL seguro (sin injection)
- [ ] Responde en lenguaje natural con los resultados

Tareas técnicas:
- [ ] Implementar QueryDetector
- [ ] Implementar SchemaDiscovery
- [ ] Implementar IntentParser
- [ ] Implementar SQLGenerator
- [ ] Implementar QueryExecutor
- [ ] Integrar en chat/service.py
- [ ] Tests unitarios e integración
```