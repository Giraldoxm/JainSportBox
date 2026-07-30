# Backend FastAPI para Render. Dockerfile explícito para evitar que el
# autodetector de la plataforma vea el proyecto .NET (servicio_biometrico/) y
# corra `dotnet restore`.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias (psycopg[binary] y boto3 no requieren libs del sistema).
COPY requirements.txt .
RUN pip install -r requirements.txt

# Solo el backend; el frontend y el bridge no van en esta imagen.
COPY backend/ ./backend/

WORKDIR /app/backend

# Render inyecta $PORT en runtime. 1 worker: el plan Starter da 0.5 CPU / 512 MB,
# y con un solo proceso el pool contra Supabase se mantiene chico y los jobs de
# APScheduler no se duplican (el advisory lock de main.py queda como red de
# seguridad por si en el futuro se sube el número de workers).
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
