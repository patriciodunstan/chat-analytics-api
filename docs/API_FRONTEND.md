# API Reference - Frontend Integration

## Base URL

```
Development: http://localhost:8000
Production:  https://your-api-domain.com
```

## Authentication

Todos los endpoints (excepto `/auth/register` y `/auth/login`) requieren token JWT en el header:

```
Authorization: Bearer <token>
```

---

## Endpoints

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
    "role": "viewer"
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
    "role": "analyst"
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
Enviar mensaje y obtener respuesta del LLM

**Request:**
```json
{
  "message": "¿Cuánto gastamos en marketing el mes pasado?",
  "conversation_id": null
}
```

- `conversation_id`: Omitir o `null` para nueva conversación

**Response (200):**
```json
{
  "conversation": {
    "id": 42,
    "title": "¿Cuánto gastamos en...",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  },
  "user_message": {
    "id": 101,
    "role": "user",
    "content": "¿Cuánto gastamos...?",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "assistant_message": {
    "id": 102,
    "role": "assistant",
    "content": "En el mes pasado, el departamento de Marketing gastó un total de $45,230...",
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
{
  "items": [
    {
      "id": 42,
      "title": "Análisis de gastos marketing",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:35:00Z",
      "message_count": 8
    }
  ],
  "total": 15,
  "skip": 0,
  "limit": 20
}
```

---

#### GET /chat/conversations/{conversation_id}
Obtener conversación con todos sus mensajes

**Response (200):**
```json
{
  "id": 42,
  "title": "Análisis de gastos marketing",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "messages": [
    {
      "id": 101,
      "role": "user",
      "content": "¿Cuánto gastamos...?",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 102,
      "role": "assistant",
      "content": "En el mes pasado...",
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
  "updated_at": "2024-01-15T11:00:00Z"
}
```

---

### 3. Data (`/data`)

> **Roles requeridos**: `analyst` o `admin` para endpoints marcados

#### GET /data/services
Listar todos los servicios

**Query Params:**
- `skip`: Default 0
- `limit`: Default 100

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Cloud Hosting",
    "description": "Servicios de infraestructura en la nube",
    "category": "Infrastructure",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

#### POST /data/services
Crear nuevo servicio `[analyst, admin]`

**Request:**
```json
{
  "name": "Marketing Digital",
  "description": "Campañas publicitarias online",
  "category": "Marketing"
}
```

**Response (201):**
```json
{
  "id": 6,
  "name": "Marketing Digital",
  "description": "Campañas publicitarias online",
  "category": "Marketing",
  "created_at": "2024-01-15T11:00:00Z"
}
```

---

#### GET /data/services/{service_id}
Obtener servicio por ID

**Response (200):**
```json
{
  "id": 1,
  "name": "Cloud Hosting",
  "description": "Servicios de infraestructura en la nube",
  "category": "Infrastructure",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

#### GET /data/services/{service_id}/costs
Obtener costos de un servicio `[analyst, admin]`

**Query Params:**
- `start_date`: ISO 8601 date (opcional)
- `end_date`: ISO 8601 date (opcional)

**Response (200):**
```json
[
  {
    "id": 1,
    "service_id": 1,
    "amount": 1500.00,
    "category": "Infrastructure",
    "description": "Servidor mensual",
    "date": "2024-01-15T00:00:00Z"
  }
]
```

---

#### POST /data/costs
Crear nuevo registro de costo `[analyst, admin]`

**Request:**
```json
{
  "service_id": 1,
  "amount": 1500.00,
  "category": "Infrastructure",
  "description": "Servidor mensual",
  "date": "2024-01-15"
}
```

**Response (201):**
```json
{
  "id": 45,
  "service_id": 1,
  "amount": 1500.00,
  "category": "Infrastructure",
  "description": "Servidor mensual",
  "date": "2024-01-15T00:00:00Z"
}
```

---

#### GET /data/services/{service_id}/expenses
Obtener gastos de un servicio `[analyst, admin]`

**Query Params:**
- `start_date`: ISO 8601 date (opcional)
- `end_date`: ISO 8601 date (opcional)

**Response (200):**
```json
[
  {
    "id": 10,
    "service_id": 1,
    "amount": 500.00,
    "category": "Maintenance",
    "description": "Soporte técnico",
    "date": "2024-01-15T00:00:00Z"
  }
]
```

---

#### POST /data/expenses
Crear nuevo registro de gasto `[analyst, admin]`

**Request:**
```json
{
  "service_id": 1,
  "amount": 500.00,
  "category": "Maintenance",
  "description": "Soporte técnico",
  "date": "2024-01-15"
}
```

---

#### GET /data/analysis/cost-vs-expense/{service_id}
Análisis de costo vs gasto `[analyst, admin]`

**Query Params:**
- `start_date`: ISO 8601 date (opcional)
- `end_date`: ISO 8601 date (opcional)

**Response (200):**
```json
{
  "service_id": 1,
  "service_name": "Cloud Hosting",
  "total_costs": 15000.00,
  "total_expenses": 3200.00,
  "costs": [...],
  "expenses": [...],
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-01-31T23:59:59Z"
}
```

---

### 4. Reports (`/reports`)

> **Roles requeridos**: `analyst` o `admin`

#### POST /reports/generate
Generar nuevo reporte PDF

**Request:**
```json
{
  "title": "Reporte Mensual Enero 2024",
  "report_type": "cost_vs_expense",
  "service_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

**Tipos de reporte:**
- `cost_vs_expense`: Comparación de costos vs gastos
- `monthly_summary`: Resumen mensual
- `service_analysis`: Análisis por servicio
- `custom`: Personalizado

**Response (202):**
```json
{
  "id": 10,
  "title": "Reporte Mensual Enero 2024",
  "report_type": "cost_vs_expense",
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
  "items": [
    {
      "id": 10,
      "title": "Reporte Mensual Enero 2024",
      "report_type": "cost_vs_expense",
      "status": "completed",
      "file_path": "/reports/reporte_20240115_120000.pdf",
      "created_at": "2024-01-15T12:00:00Z"
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 20
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
  "report_type": "cost_vs_expense",
  "status": "completed",
  "file_path": "/reports/reporte_20240115_120000.pdf",
  "analysis_summary": "El costo total fue de $15,000 con un aumento del 12%...",
  "created_at": "2024-01-15T12:00:00Z"
}
```

---

#### GET /reports/{report_id}/download
Descargar archivo PDF del reporte

**Response (200):**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="reporte_20240115_120000.pdf"

<binary pdf data>
```

---

### 5. Health (`/health`)

#### GET /health
Verificar estado del servicio

**Response (200):**
```json
{
  "status": "healthy",
  "environment": "development"
}
```

---

## Roles y Permisos

| Rol | Permisos |
|-----|----------|
| **VIEWER** | - Ver servicios<br>- Chat con LLM<br>- Ver reportes propios |
| **ANALYST** | - Todo de VIEWER<br>- Crear/editar servicios<br>- Crear costos/gastos<br>- Ver análisis de datos<br>- Generar reportes |
| **ADMIN** | - Todos los permisos |

---

## Errores

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

---

## Diagrama de Flujo de Autenticación

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
      │ access_token
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

## Ejemplo de Integración Frontend (JavaScript/TypeScript)

```typescript
// Configuración
const API_BASE = 'http://localhost:8000';

// Cliente con interceptor
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
  service_id: number;
  start_date: string;
  end_date: string;
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