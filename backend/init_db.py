"""
Script para inicializar la base de datos.
Crea todas las tablas definidas en models.py.
"""

from database import engine
from models import Base


def main():
    print("Creando tablas en crossfit.db ...")
    Base.metadata.create_all(bind=engine)
    print("Todas las tablas fueron creadas exitosamente!")

    # Mostrar las tablas creadas
    for table_name in Base.metadata.tables:
        print(f"   - {table_name}")


if __name__ == "__main__":
    main()
