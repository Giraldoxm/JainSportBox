"""Siembra movimientos financieros de mentira para poder mirar el módulo con datos.

SOLO CORRE SOBRE SQLITE. Si `DATABASE_URL` apunta a Postgres (Supabase), aborta:
esto mete plata inventada en el libro contable y en producción sería un desastre.

Todos los movimientos llevan la marca `[demo]` en `notas`, así que se pueden borrar
después sin tocar los reales:

    ..\\venv\\Scripts\\python.exe scripts\\seed_demo_finanzas.py            # sembrar
    ..\\venv\\Scripts\\python.exe scripts\\seed_demo_finanzas.py --limpiar  # borrar
"""
import os
import random
import sys
from datetime import datetime, timedelta

# El script vive en backend/scripts/, pero los módulos están en backend/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine  # noqa: E402
from models import MovimientoFinanciero, RolUsuario, TipoMovimiento, Usuario  # noqa: E402

MARCA = "[demo]"

# (categoría, concepto, monto mínimo, monto máximo, cada cuántos meses)
EGRESOS = [
    ("renta",         "Renta del local",              1_800_000, 1_800_000, 1),
    ("nomina",        "Salarios de coaches",          1_200_000, 1_600_000, 1),
    ("servicios",     "Luz, agua e internet",           180_000,   320_000, 1),
    ("mantenimiento", "Mantenimiento de máquinas",       80_000,   250_000, 2),
    ("marketing",     "Pauta en redes",                 120_000,   400_000, 2),
    ("equipamiento",  "Compra de discos y barras",      350_000, 1_100_000, 4),
    ("otros",         "Gastos varios del box",           40_000,   150_000, 3),
]

INGRESOS = [
    ("ingreso_varios", "Alquiler del box para evento",  200_000,   600_000, 3),
    ("ingreso_varios", "Patrocinio local",              300_000,   800_000, 6),
    ("mensualidad",    "Membresía pagada por fuera",    100_000,   200_000, 2),
]

MESES = 12


def _limpiar(db) -> int:
    demo = db.query(MovimientoFinanciero).filter(MovimientoFinanciero.notas.like(f"{MARCA}%")).all()
    for m in demo:
        db.delete(m)
    db.commit()
    return len(demo)


def sembrar(limpiar_solo: bool = False) -> None:
    backend = engine.url.get_backend_name()
    if backend != "sqlite":
        print(f"ABORTA: la base es '{backend}', no sqlite. Esto solo corre en local.")
        print(f"  {engine.url.render_as_string(hide_password=True)}")
        sys.exit(1)

    print(f"Base de datos: {engine.url.render_as_string(hide_password=True)}")
    db = SessionLocal()
    try:
        borrados = _limpiar(db)
        if borrados:
            print(f"  - {borrados} movimientos [demo] anteriores eliminados")
        if limpiar_solo:
            print("Listo (solo limpieza).")
            return

        admin = db.query(Usuario).filter(Usuario.rol == RolUsuario.ADMIN).first()
        rnd = random.Random(42)   # semilla fija: dos corridas dan los mismos números
        hoy = datetime.utcnow()
        creados = 0

        for mes_atras in range(MESES):
            base = hoy - timedelta(days=30 * mes_atras)
            for tipo, catalogo in (("egreso", EGRESOS), ("ingreso", INGRESOS)):
                for categoria, concepto, minimo, maximo, cada in catalogo:
                    if mes_atras % cada:
                        continue
                    dia = rnd.randint(1, 27)
                    fecha = base.replace(day=min(dia, 28), hour=rnd.randint(8, 19), minute=rnd.randint(0, 59))
                    if fecha > hoy:
                        continue
                    db.add(MovimientoFinanciero(
                        tipo=TipoMovimiento(tipo),
                        concepto=concepto,
                        categoria=categoria,
                        # Redondeado al millar: los montos con centavos ensucian la lectura.
                        monto=round(rnd.randint(minimo, maximo), -3),
                        fecha=fecha,
                        metodo_pago=rnd.choice(["efectivo", "transferencia"]),
                        notas=f"{MARCA} generado por seed_demo_finanzas.py",
                        fuente="manual",
                        created_by=admin.id if admin else None,
                    ))
                    creados += 1

        db.commit()
        print(f"  + {creados} movimientos [demo] creados en los últimos {MESES} meses")
        print("\nPara borrarlos: python scripts/seed_demo_finanzas.py --limpiar")
    finally:
        db.close()


if __name__ == "__main__":
    sembrar(limpiar_solo="--limpiar" in sys.argv)
