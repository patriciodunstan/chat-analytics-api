# Dockerfile multi-stage para producción optimizada
FROM python:3.11-slim as base

# Variables de entorno para Python (sin PORT)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Directorio de trabajo
WORKDIR /app

# ================================
# Stage: dependencies
# ================================
FROM base as dependencies

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo requirements para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# ================================
# Stage: runtime
# ================================
FROM base as runtime

# Instalar solo librerías runtime (sin compiladores)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias instaladas desde stage anterior
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Crear directorio para reportes generados
RUN mkdir -p /app/reports_output && chown -R appuser:appuser /app/reports_output

# Dar permisos de ejecución solo a start.sh
RUN chmod +x /app/start.sh

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check (puerto fijo 8000)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

# Comando por defecto - puerto fijo 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
