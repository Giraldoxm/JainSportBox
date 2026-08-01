import os
from dotenv import load_dotenv

load_dotenv()

from database import SessionLocal
from models import Ejercicio, Plan, Usuario, RolUsuario
from security import get_password_hash

import json as _json

PLANES_DEFAULT = [
    {
        "nombre": "1 Semana", "precio": 35000, "duracion_dias": 7,
        "descripcion": "Acceso por 7 días",
        "beneficios": _json.dumps(["Acceso al box 7 días", "Clases grupales incluidas", "Uso de equipamiento completo"]),
    },
    {
        "nombre": "15 Días", "precio": 60000, "duracion_dias": 15,
        "descripcion": "Acceso por quince días",
        "beneficios": _json.dumps(["Acceso al box 15 días", "Clases grupales incluidas", "Uso de equipamiento completo", "Seguimiento de progreso"]),
    },
    {
        "nombre": "1 Mes", "precio": 100000, "duracion_dias": 30,
        "descripcion": "Acceso por un mes",
        "beneficios": _json.dumps(["Acceso ilimitado al box", "Clases grupales incluidas", "Uso de equipamiento completo", "Seguimiento de progreso", "Asesoría nutricional básica"]),
    },
]

# Movimientos base de CrossFit para que el box pueda armar WODs desde el primer
# arranque. La categoria debe ser una de las cinco que filtra el router y colorea
# EjerciciosView: Cardio | Fuerza | Gimnasia | Olimpico | Otro.
# Los nombres que se solapan con Mis Marcas van identicos a ejerciciosMarcas.js.
EJERCICIOS_DEFAULT = [
    # ── Olímpico ───────────────────────────────────────────────
    ("Snatch",            "Olímpico", "Arranque: de suelo a por encima de la cabeza en un solo movimiento"),
    ("Clean",             "Olímpico", "Cargada: de suelo a posición de rack delantero"),
    ("Clean and Jerk",    "Olímpico", "Cargada seguida de envión por encima de la cabeza"),
    ("Power Clean",       "Olímpico", "Cargada recibida por encima del paralelo, sin sentadilla completa"),

    # ── Fuerza ─────────────────────────────────────────────────
    ("Back Squat",        "Fuerza",   "Sentadilla con la barra apoyada en la espalda"),
    ("Front Squat",       "Fuerza",   "Sentadilla con la barra en posición de rack delantero"),
    ("Overhead Squat",    "Fuerza",   "Sentadilla sosteniendo la barra por encima de la cabeza"),
    ("Deadlift",          "Fuerza",   "Peso muerto: levantar la barra del suelo hasta la cadera"),
    ("Bench Press",       "Fuerza",   "Press de banca acostado"),
    ("Press Militar",     "Fuerza",   "Press estricto de hombros, sin impulso de piernas"),
    ("Push Press",        "Fuerza",   "Press de hombros con impulso de piernas"),
    ("Thruster",          "Fuerza",   "Front squat encadenado con press por encima de la cabeza"),
    ("Kettlebell Swing",  "Fuerza",   "Balanceo de pesa rusa impulsado por la cadera"),
    ("Wall Ball",         "Fuerza",   "Squat con balón medicinal lanzado al objetivo en la pared"),

    # ── Gimnasia ───────────────────────────────────────────────
    ("Dominadas",         "Gimnasia", "Tracción en barra hasta pasar el mentón"),
    ("Toes to Bar",       "Gimnasia", "Colgado de la barra, llevar los pies hasta tocarla"),
    ("Muscle Up",         "Gimnasia", "Tracción y transición a fondo por encima de la barra o anillas"),
    ("Handstand Push Up", "Gimnasia", "Flexión de brazos en parada de manos"),
    ("Burpee",            "Gimnasia", "Del suelo (pecho abajo) al salto con palmada arriba"),
    ("Push Up",           "Gimnasia", "Flexión de brazos con el cuerpo alineado"),
    ("Air Squat",         "Gimnasia", "Sentadilla sin peso, cadera por debajo de la rodilla"),
    ("Sit Up",            "Gimnasia", "Abdominal completo hasta tocar los pies"),
    ("Box Jump",          "Gimnasia", "Salto al cajón con extensión completa de cadera arriba"),

    # ── Cardio ─────────────────────────────────────────────────
    ("Remo",              "Cardio",   "Remo en máquina, medido en metros o calorías"),
    ("Carrera",           "Cardio",   "Carrera continua, medida en metros"),
    ("Assault Bike",      "Cardio",   "Bicicleta de aire, medida en calorías"),
    ("Double Under",      "Cardio",   "Salto de cuerda con dos pasadas por salto"),
]


def _admin_config() -> dict:
    return {
        "nombre":              os.environ["ADMIN_NOMBRE"],
        "email":               os.environ["ADMIN_EMAIL"],
        "password":            os.environ["ADMIN_PASSWORD"],
        "rol":                 RolUsuario.ADMIN,
        "telefono":            os.environ["ADMIN_TELEFONO"],
        "documento_identidad": os.environ["ADMIN_DOCUMENTO"],
    }

def seed_planes():
    db = SessionLocal()
    try:
        for datos in PLANES_DEFAULT:
            plan = db.query(Plan).filter(Plan.nombre == datos["nombre"]).first()
            if not plan:
                db.add(Plan(**datos))
                print(f"  + Plan '{datos['nombre']}' creado")
            elif not plan.beneficios:
                plan.beneficios = datos["beneficios"]
                print(f"  · Plan '{datos['nombre']}' actualizado con beneficios")
            else:
                print(f"  · Plan '{datos['nombre']}' ya existe")
        db.commit()
    finally:
        db.close()


def seed_ejercicios():
    """Siembra el catálogo base, solo si la tabla está vacía.

    A diferencia de seed_planes, no reconcilia ejercicio por ejercicio: si el
    coach borra uno sembrado, no debe reaparecer en el próximo arranque.
    """
    db = SessionLocal()
    try:
        if db.query(Ejercicio).count() > 0:
            print("  · Catálogo de ejercicios ya poblado, se omite")
            return
        db.add_all(
            Ejercicio(nombre=nombre, categoria=categoria, descripcion=descripcion)
            for nombre, categoria, descripcion in EJERCICIOS_DEFAULT
        )
        db.commit()
        print(f"  + {len(EJERCICIOS_DEFAULT)} ejercicios sembrados")
    finally:
        db.close()


def seed_admin():
    cfg = _admin_config()
    db = SessionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.email == cfg["email"]).first()
        if not admin:
            admin = Usuario(
                nombre=cfg["nombre"],
                email=cfg["email"],
                password_hash=get_password_hash(cfg["password"]),
                documento_identidad=cfg["documento_identidad"],
                rol=cfg["rol"],
                telefono=cfg["telefono"],
            )
            db.add(admin)
            db.commit()
            print(f"  + Usuario admin '{cfg['email']}' creado")
        else:
            if not admin.documento_identidad:
                admin.documento_identidad = cfg["documento_identidad"]
                db.commit()
                print(f"  · Admin actualizado con documento de identidad")
            else:
                print(f"  · Usuario admin '{cfg['email']}' ya existe")
    finally:
        db.close()


if __name__ == "__main__":
    print("Sembrando planes por defecto...")
    seed_planes()
    print("Sembrando usuario admin...")
    seed_admin()
    print("Sembrando catalogo de ejercicios...")
    seed_ejercicios()
    print("Listo.")
