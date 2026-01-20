# API Reference - Frontend Integration (Estado Actual)

**Versión**: 0.1.0
**Última actualización**: 2026-01-19

> ℹ️ Esta documentación refleja **únicamente los endpoints implementados** en el código actual.

---

## Base URL

```
Development: http://localhost:8000
Production:  https://tu-api-domain.com
```

## Swagger Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Authentication

Todos los endpoints (excepto `/auth/register` y `/auth/login`) requieren token JWT en el header:

```http
Authorization: Bearer <token>
```

---

## Endpoints Implementados

### 1. Authentication (`/auth`)

#### POST /auth/register

Registrar nuevo usuario (rol por defecto: VIEWER)

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "viewer",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

#### POST /auth/login

Iniciar sesión

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "analyst",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

#### GET /auth/me

Obtener usuario actual (requiere token)

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### 2. Chat (`/chat`)

#### POST /chat/message

Enviar mensaje y obtener respuesta del LLM con NL2SQL

**Request:**
```json
{
  "message": "¿Cuántos equipos fallaron en enero de 2024?",
  "conversation_id": null
}
```

- `conversation_id`: Omitir o `null` para nueva conversación

**Response (200):**
```json
{
  "conversation_id": 42,
  "user_message": {
    "id": 101,
    "conversation_id": 42,
    "role": "user",
    "content": "¿Cuántos equipos fallaron...?",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "assistant_message": {
    "id": 102,
    "conversation_id": 42,
    "role": "assistant",
    "content": "En enero de 2024, se registraron 15 fallos en equipos...",
    "created_at": "2024-01-15T10:30:05Z"
  }
}
```

---

#### GET /chat/conversations

Listar conversaciones del usuario (paginado)

**Query Params:**
- `skip`: Número de registros a saltar (default: 0)
- `limit`: Número máximo de registros (default: 20)

**Response (200):**
```json
[
  {
    "id": 42,
    "title": "Análisis de fallos en equipos",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "message_count": 8
  }
]
```

---

#### GET /chat/conversations/{conversation_id}

Obtener conversación con todos sus mensajes

**Response (200):**
```json
{
  "id": 42,
  "title": "Análisis de fallos en equipos",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "message_count": 8,
  "messages": [
    {
      "id": 101,
      "conversation_id": 42,
      "role": "user",
      "content": "¿Cuántos equipos...?",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 102,
      "conversation_id": 42,
      "role": "assistant",
      "content": "En enero de 2024...",
      "created_at": "2024-01-15T10:30:05Z"
    }
  ]
}
```

---

#### POST /chat/conversations

Crear nueva conversación

**Request:**
```json
{
  "title": "Análisis Q4 2024"
}
```

**Response (201):**
```json
{
  "id": 43,
  "title": "Análisis Q4 2024",
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "message_count": 0
}
```

---

### 3. Reports (`/reports`)

> **Roles requeridos**: `analyst` o `admin` para generar reportes

#### POST /reports/generate

Generar nuevo reporte PDF

**Request:**
```json
{
  "title": "Reporte Mensual Enero 2024",
  "report_type": "data_summary"
}
```

**Tipos de reporte disponibles:**
- `data_summary`: Resumen de datos
- `trend_analysis`: Análisis de tendencias
- `custom`: Personalizado

**Response (201):**
```json
{
  "id": 10,
  "title": "Reporte Mensual Enero 2024",
  "report_type": "data_summary",
  "status": "processing",
  "file_path": null,
  "analysis_summary": null,
  "created_at": "2024-01-15T12:00:00Z"
}
```

> **Nota**: El reporte se genera de forma asíncrona. El estado cambia de `processing` a `completed`.

---

#### GET /reports/list

Listar reportes del usuario

**Query Params:**
- `skip`: Default 0
- `limit`: Default 20

**Response (200):**
```json
{
  "reports": [
    {
      "id": 10,
      "title": "Reporte Mensual Enero 2024",
      "report_type": "data_summary",
      "status": "completed",
      "file_path": "/reports/reporte_20240115_120000.pdf",
      "analysis_summary": "Resumen del análisis...",
      "created_at": "2024-01-15T12:00:00Z"
    }
  ],
  "total": 5
}
```

---

#### GET /reports/{report_id}

Obtener información de un reporte

**Response (200):**
```json
{
  "id": 10,
  "title": "Reporte Mensual Enero 2024",
  "report_type": "data_summary",
  "status": "completed",
  "file_path": "/reports/reporte_20240115_120000.pdf",
  "analysis_summary": "El análisis muestra...",
  "created_at": "2024-01-15T12:00:00Z"
}
```

---

#### GET /reports/{report_id}/download

Descargar archivo PDF del reporte

**Response (200):**
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="reporte_20240115_120000.pdf"

<binary pdf data>
```

---

### 4. Health (`/health`)

#### GET /health

Verificar estado del servicio (sin autenticación)

**Response (200):**
```json
{
  "status": "healthy",
  "environment": "development"
}
```

---

## Datasets Disponibles para NL2SQL

El sistema puede responder preguntas en lenguaje natural sobre las siguientes tablas:

### Mining Domain

| Tabla | Descripción | Registros |
|-------|-------------|-----------|
| `equipment` | Equipos industriales (excavadoras, camiones, etc.) | Variable |
| `maintenance_events` | Eventos de mantenimiento programado y correctivo | Variable |
| `failure_events` | Fallos y averías de equipos | Variable |

**Campos principales:**
- `equipment`: equipment_id, tipo_maquina, marca, modelo, ano
- `maintenance_events`: fecha, tipo_intervencion, costo_total, duracion_horas
- `failure_events`: fecha, codigo_falla, descripcion_falla, causa_raiz, impacto

### Support Domain

| Tabla | Descripción | Registros |
|-------|-------------|-----------|
| `support_tickets` | Tickets de soporte técnico de clientes | ~8,000 |

**Campos principales:**
- ticket_id, customer_name, customer_email
- ticket_type, ticket_subject, ticket_status
- ticket_priority, ticket_channel
- customer_satisfaction_rating

### Ejemplos de Preguntas NL2SQL

```
"¿Cuántos equipos de tipo excavadora tenemos?"
"¿Cuál es el costo promedio de mantenimiento preventivo?"
"Muestra los fallos más frecuentes en los últimos 6 meses"
"¿Cuántos tickets están pendientes de resolución?"
"¿Cuál es el rating promedio de satisfacción de clientes?"
```

---

## Roles y Permisos

| Rol | Permisos |
|-----|----------|
| **VIEWER** | - Ver conversaciones propias<br>- Chatear con LLM<br>- Ver reportes propios |
| **ANALYST** | - Todo de VIEWER<br>- Generar reportes |
| **ADMIN** | - Todos los permisos |

---

## Errores Comunes

### 400 Bad Request

```json
{
  "detail": "Validation error"
}
```

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

```json
{
  "detail": "Error processing message: [error details]"
}
```

---

## Flujo de Autenticación

```
┌─────────┐
│ Frontend│
└────┬────┘
     │ POST /auth/login
     │ {email, password}
     ▼
┌─────────────┐
│   API Auth  │
└─────┬───────┘
      │ {access_token, user}
      ▼
┌─────────────┐
│  Frontend   │
│ (Store Token)│
└─────┬───────┘
      │ Authorization: Bearer <token>
      ▼
┌─────────────┐
│ API Endpoints│
│ (Protected)  │
└─────────────┘
```

---

## Ejemplo de Integración Frontend (TypeScript)

```typescript
// Configuración
const API_BASE = 'http://localhost:8000';

// Cliente axios con interceptor
const api = axios.create({
  baseURL: API_BASE,
});

// Interceptor para agregar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Login
async function login(email: string, password: string) {
  const { data } = await api.post('/auth/login', { email, password });
  localStorage.setItem('access_token', data.access_token);
  return data.user;
}

// Enviar mensaje de chat
async function sendMessage(message: string, conversationId?: number) {
  const { data } = await api.post('/chat/message', {
    message,
    conversation_id: conversationId || null,
  });
  return data;
}

// Listar conversaciones
async function getConversations(skip = 0, limit = 20) {
  const { data } = await api.get('/chat/conversations', {
    params: { skip, limit }
  });
  return data;
}

// Generar reporte
async function generateReport(params: {
  title: string;
  report_type: string;
}) {
  const { data } = await api.post('/reports/generate', params);
  return data;
}

// Descargar reporte
async function downloadReport(reportId: number) {
  const { data } = await api.get(`/reports/${reportId}/download`, {
    responseType: 'blob'
  });
  const url = window.URL.createObjectURL(new Blob([data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `report_${reportId}.pdf`);
  document.body.appendChild(link);
  link.click();
}
```

---

## Notas Importantes

### ⚠️ Endpoints No Implementados

#### Endpoints Removidos (no implementados)

Los siguientes endpoints **NO EXISTEN** en el código actual:
- ❌ `/data/services` (todos los métodos)
- ❌ `/data/costs`
- ❌ `/data/expenses`
- ❌ `/data/analysis/cost-vs-expense/{service_id}`

Si necesitas esta funcionalidad, debes implementar el módulo `/data` o usar el sistema NL2SQL para consultar los datasets existentes.

#### Tipos de Reportes

**Antes (documentado)**:
- `cost_vs_expense`, `monthly_summary`, `service_analysis`, `custom`

**Ahora (implementado)**:
- `data_summary`, `trend_analysis`, `custom`

---

## Contribuir

Si encuentras discrepancias entre esta documentación y el código:

1. Verificar en Swagger UI: http://localhost:8000/docs
2. Revisar el código fuente en `app/*/router.py`
3. Reportar issue en el repositorio

---

## Referencias

- Swagger UI: http://localhost:8000/docs - Documentación interactiva
- ReDoc: http://localhost:8000/redoc - Documentación alternativa
- [Setup Guide](../SETUP.md) - Instalación y configuración
- [README](../README.md) - Overview del proyecto
