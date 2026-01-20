# Estado del Proyecto - Chat Analytics API (NL2SQL)

## Fecha: 2025-01-19

---

## 🎯 Propósito del Proyecto

**POC de NL2SQL Genérico** - Un asistente de datos que se adapta a CUALQUIER base de datos del cliente mediante auto-descubrimiento de esquema.

**Diferenciador**: El cliente conecta SU base de datos PostgreSQL y puede hacer preguntas en español inmediatamente, sin configuración manual de esquemas.

---

## 📊 Datasets de Demostración

### Dataset 1: Minería (Mantenimiento de Maquinaria Pesada)
```
equipment (50 registros)
├── equipment_id, tipo_maquina, marca, modelo, año

maintenance_events (5,000 registros)
├── equipment_id, fecha, tipo_intervencion, descripcion_tarea
├── horas_operacion, costo_total, duracion_horas
└── responsable, ubicacion_gps

failure_events (3,000 registros)
├── equipment_id, fecha, codigo_falla, descripcion_falla
├── causa_raiz, horas_operacion, costo_total
└── duracion_horas, responsable, impacto
```

**Preguntas ejemplo:**
- "¿Cuál es el costo total de mantenimiento por tipo de máquina?"
- "¿Qué equipos tienen más fallas por sobrecalentamiento?"
- "Muéstrame la tendencia de fallas en los últimos 6 meses"

### Dataset 2: Soporte al Cliente
```
support_tickets (~8,000 registros)
├── ticket_id, customer_name, customer_email, ticket_type
├── ticket_subject, ticket_description, ticket_status
├── ticket_priority, ticket_channel, first_response_time
└── customer_satisfaction_rating
```

**Preguntas ejemplo:**
- "¿Cuántos tickets críticos están abiertos?"
- "¿Cuál es el tiempo promedio de resolución por canal?"
- "¿Qué productos generan más tickets técnicos?"

---

## ✅ Módulos Implementados

### 1. Autenticación (`app/auth/`)
| Archivo | Estado | Descripción |
|---------|--------|-------------|
| `router.py` | ✅ | register, login, me |
| `service.py` | ✅ | Lógica de usuarios y bcrypt |
| `jwt_handler.py` | ✅ | Gestión de tokens JWT |
| `dependencies.py` | ✅ | get_current_user, require_analyst |
| `schemas.py` | ✅ | UserCreate, UserLogin, UserResponse |

**Roles**: VIEWER, ANALYST, ADMIN

---

### 2. Chat + NL2SQL (`app/chat/`)
| Archivo | Estado | Descripción |
|---------|--------|-------------|
| `router.py` | ✅ | message, conversations |
| `service.py` | ✅ | NL2SQL integrado |
| `schemas.py` | ✅ | ChatRequest, ChatResponse |
| `llm/gemini_client.py` | ✅ | Cliente Gemini |

**NL2SQL (`app/chat/nl2sql/`)**:
| Archivo | Estado |
|---------|--------|
| `schemas.py` | ✅ DatabaseSchema, TableInfo, ParsedIntent |
| `exceptions.py` | ✅ NL2SQLError, SchemaDiscoveryError |
| `prompts.py` | ✅ Prompts para Gemini |
| `detector.py` | ✅ QueryDetector |
| `schema_discovery.py` | ✅ Auto-descubrimiento de esquema |
| `intent_parser.py` | ✅ Parser dinámico |
| `sql_generator.py` | ✅ Generador SQL genérico |
| `query_executor.py` | ✅ Ejecutor seguro |

---

### 3. Reports (`app/reports/`)
| Archivo | Estado | Descripción |
|---------|--------|-------------|
| `router.py` | ✅ | generate, list, download |
| `service.py` | ✅ | Generación de reportes |
| `generator.py` | ✅ | PDF genérico |
| `charts.py` | ✅ | Gráficos matplotlib |
| `schemas.py` | ✅ | ReportRequest, ReportResponse |

---

### 4. Base de Datos (`app/db/`)
| Archivo | Modelos |
|---------|---------|
| `models.py` | User, Conversation, Message, Report, Equipment, MaintenanceEvent, FailureEvent, SupportTicket |
| `database.py` | AsyncSession, engine |
| `seed.py` | Seed de usuarios |

---

## 📁 Estructura del Proyecto

```
app/
├── auth/              # JWT + roles
├── chat/
│   ├── nl2sql/         # NL2SQL completo
│   └── llm/            # Gemini client
├── reports/           # PDF reports
├── db/                # SQLAlchemy models
├── config.py          # Settings
└── main.py            # FastAPI app

docs/
├── NL2SQL_GUIA.md      # Guía NL2SQL
├── API_FRONTEND.md     # API para frontend
└── ESTADO_PROYECTO.md # Este archivo

scripts/
├── seed_equipment.sql # Seed minería
└── seed_tickets.py     # Seed soporte

tests/
├── test_auth.py       # 6 tests ✅
├── test_chat.py       # 7 tests ✅
├── test_nl2sql.py     # 6 tests ✅
├── test_reports.py    # 7 tests ✅
└── test_services.py   # 12 tests ✅
```

---

## 📋 Endpoints API (13 totales)

| Módulo | Método | Endpoint | Auth |
|--------|--------|----------|------|
| Auth | POST | `/auth/register` | ❌ |
| Auth | POST | `/auth/login` | ❌ |
| Auth | GET | `/auth/me` | ✅ |
| Chat | POST | `/chat/message` | ✅ |
| Chat | GET | `/chat/conversations` | ✅ |
| Chat | GET | `/chat/conversations/{id}` | ✅ |
| Chat | POST | `/chat/conversations` | ✅ |
| Reports | POST | `/reports/generate` | ANALYST+ |
| Reports | GET | `/reports/list` | ✅ |
| Reports | GET | `/reports/{id}` | ✅ |
| Reports | GET | `/reports/{id}/download` | ✅ |
| Health | GET | `/health` | ❌ |

---

## 🧪 Tests

**38 tests pasando** ✅

```
test_auth.py              6/6 pass
test_chat.py              7/7 pass
test_nl2sql.py            6/6 pass
test_reports.py           7/7 pass
test_services.py         12/12 pass
```

---

## 🚀 Para Probar

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar servidor
uvicorn app.main:app --reload

# 3. Crear base de datos y cargar seeds
python -m app.db.seed

# 4. Cargar datos de demostración
psql -U user -d db -f scripts/seed_equipment.sql
python scripts/seed_tickets.py

# 5. Ejecutar tests
pytest -v
```

---

## 🎛️ Roles y Permisos

| Rol | Permisos |
|-----|----------|
| **VIEWER** | - Chat con LLM<br>- Ver reportes propios |
| **ANALYST** | - Todo de VIEWER<br>- Generar reportes |
| **ADMIN** | - Todos los permisos |

---

## 💡 Valor Comercial

```
ANTES: "Chat con datos financieros hardcodeados"
DESPUÉS: "Asistente de datos que se adapta a CUALQUIER base de datos"
```

**Ejemplo de uso:**
```
Usuario: "¿Cuántos tickets abiertos hay por prioridad?"

Sistema:
"📊 Tickets abiertos por prioridad:

| Prioridad | Cantidad |
|-----------|----------|
| Critical  | 12       |
| High      | 45       |
| Medium    | 128      |
| Low       | 89       |

Total: 274 tickets abiertos"
```