"""
Inserta los planes por defecto si no existen.
"""
from database import SessionLocal
from models import Plan

PLANES_DEFAULT = [
    {"nombre": "1 Día",    "precio": 5000,  "duracion_dias": 1,  "descripcion": "Acceso por un día"},
    {"nombre": "15 Días",  "precio": 60000, "duracion_dias": 15, "descripcion": "Acceso por quince días"},
    {"nombre": "30 Días",  "precio": 100000,"duracion_dias": 30, "descripcion": "Acceso mensual"},
]

def seed_planes():
    db = SessionLocal()
    try:
        for datos in PLANES_DEFAULT:
            existe = db.query(Plan).filter(Plan.nombre == datos["nombre"]).first()
            if not existe:
                db.add(Plan(**datos))
                print(f"  + Plan '{datos['nombre']}' creado")
            else:
                print(f"  · Plan '{datos['nombre']}' ya existe")
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    print("Sembrando planes por defecto...")
    seed_planes()
    print("Listo.")
