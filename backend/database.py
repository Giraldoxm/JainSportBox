"""
Configuración de la conexión a la base de datos.

Lee DATABASE_URL del entorno. Por defecto usa SQLite local; en producción
(Render) se inyecta la URI de Postgres de Supabase.

Importante: usar el pooler de Supabase en modo *session* (puerto 5432), no el de
modo *transaction* (6543). El scheduler de main.py toma un pg_try_advisory_lock a
nivel de sesión sobre una conexión persistente, y el modo transaction lo liberaría
al terminar cada consulta (además de romper los prepared statements de psycopg3).
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///crossfit.db")
# La URI puede venir como "postgres://" o "postgresql://"; forzamos el driver
# psycopg v3 (psycopg2 no está instalado, solo psycopg[binary]).
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_es_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if _es_sqlite else {}

# El default de psycopg es sslmode=prefer, que acepta caer a texto plano sin avisar.
# Como la conexión sale de Render hacia Supabase por internet abierta, se exige TLS.
if not _es_sqlite and "sslmode=" not in DATABASE_URL:
    DATABASE_URL += ("&" if "?" in DATABASE_URL else "?") + "sslmode=require"

# Pool explícito solo para Postgres (SQLite no usa pool de conexiones). Dimensionado
# para el plan free de Supabase y 1 worker de uvicorn; ajustable por entorno sin
# reconstruir la imagen. pool_recycle porque Supavisor corta conexiones ociosas.
_pool_kwargs = (
    {}
    if _es_sqlite
    else {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "3")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "2")),
        "pool_recycle": 300,
    }
)

engine = create_engine(
    DATABASE_URL,
    echo=_es_sqlite,
    connect_args=connect_args,
    pool_pre_ping=True,
    **_pool_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Generador de sesiones para inyección de dependencias."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
