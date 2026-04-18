"""
Configuración de la conexión a la base de datos SQLite.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///crossfit.db"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Generador de sesiones para inyección de dependencias."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
