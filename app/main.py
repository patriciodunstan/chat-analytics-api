"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.reports.router import router as reports_router
from app.db.database import init_db


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Chat Analytics API",
    description="""
    Backend FastAPI para consultas de datos en lenguaje natural con LLM.

    ## Características

    - **NL2SQL**: Consultas en español sobre cualquier base de datos
    - **Auto-descubrimiento**: Detecta automáticamente el esquema de la DB
    - **Chat con LLM**: Integración con Google Gemini
    - **Reportes PDF**: Generación automática con gráficos
    - **Autenticación JWT**: Roles (VIEWER, ANALYST, ADMIN)

    ## Autenticación

    Todos los endpoints (excepto `/auth/register` y `/auth/login`) requieren token JWT:

    ```
    Authorization: Bearer <token>
    ```

    ## Datasets disponibles

    - **Minería**: equipment, maintenance_events, failure_events
    - **Soporte**: support_tickets (~8,000 registros)
    """,
    version="0.1.0",
    lifespan=lifespan,
    contact={
        "name": "Chat Analytics API",
        "url": "https://github.com/tu-usuario/chat-analytics-api",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(reports_router, prefix="/reports", tags=["Reports"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.environment}
