from database import SessionLocal
from models import Plan

PLANES_DEFAULT = [
    {"nombre": "1 Semana",  "precio": 35000,  "duracion_dias": 7,  "descripcion": "Acceso por 7 días"},
    {"nombre": "15 Días",   "precio": 60000,  "duracion_dias": 15, "descripcion": "Acceso por quince días"},
    {"nombre": "1 Mes",     "precio": 100000, "duracion_dias": 30, "descripcion": "Acceso por un mes"},
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
