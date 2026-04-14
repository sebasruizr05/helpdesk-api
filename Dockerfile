# ============ STAGE 1: BUILDER ============
# Este stage solo instala las dependencias de Python
FROM python:3.11-slim as builder

WORKDIR /app

# Copiar archivo de dependencias
COPY requirements.txt .

# Crear entorno virtual e instalar paquetes
# Esto reduce el tamaño final porque no incluimos archivos temporales
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt


# ============ STAGE 2: FINAL ============
# Este stage es la imagen final que se ejecutará
FROM python:3.11-slim

WORKDIR /app

# Copiar solo el entorno virtual compilado del builder
COPY --from=builder /opt/venv /opt/venv

# Configurar variables de entorno
# PYTHONUNBUFFERED: ver output de Python en tiempo real
# PYTHONDONTWRITEBYTECODE: no crear archivos .pyc
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copiar código de la aplicación
COPY . .

# Puerto que expone la aplicación
EXPOSE 8000

# Health check: verifica que la API esté respondiendo
# Si falla 3 veces, Docker considera que el contenedor no está sano
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-8000}/api/v2/', timeout=5)" || exit 1

# Comando de inicio:
# 1. Ejecuta migraciones de BD
# 2. Inicia gunicorn con 3 workers y 2 threads
CMD sh -c "python manage.py migrate && gunicorn helpdesk.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --threads 2 --worker-class gthread --max-requests 1000 --max-requests-jitter 100"
