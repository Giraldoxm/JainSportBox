import models
from database import engine, SessionLocal
from sqlalchemy import text

models.Base.metadata.create_all(bind=engine)

# Migraciones ligeras para columnas nuevas
_migraciones = [
    "ALTER TABLE productos ADD COLUMN foto_url VARCHAR(300)",
    "ALTER TABLE usuarios ADD COLUMN telefono VARCHAR(20)",
    "ALTER TABLE ventas ADD COLUMN metodo_pago VARCHAR(50)",
]
with engine.connect() as _conn:
    for _sql in _migraciones:
        try:
            _conn.execute(text(_sql))
            _conn.commit()
        except Exception:
            pass

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from routers import alertas, asistencia, auth, finanzas, pagos, planes, productos, salud, usuarios, ventas, wods
from seed import seed_planes

seed_planes()

app = FastAPI(
    title="CrossFit Box System",
    description="API para la gestion integral de un box de CrossFit",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


# ── Scheduler diario de alertas ───────────────────────────────
def _job_alertas():
    db = SessionLocal()
    try:
        from routers.alertas import generar_alertas
        creadas = generar_alertas(db)
        if creadas:
            print(f"[Scheduler] {creadas} alerta(s) de membresía generada(s).")
    finally:
        db.close()

_scheduler = BackgroundScheduler(timezone="America/Bogota")
# Ejecuta todos los días a las 9:00 AM
_scheduler.add_job(_job_alertas, CronTrigger(hour=9, minute=0))
# También al arrancar para no perder el día actual
_scheduler.add_job(_job_alertas, "date")
_scheduler.start()


@app.on_event("shutdown")
def _shutdown():
    _scheduler.shutdown(wait=False)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Gym System Online"}


app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(productos.router)
app.include_router(ventas.router)
app.include_router(wods.router)
app.include_router(planes.router)
app.include_router(pagos.router)
app.include_router(asistencia.router)
app.include_router(finanzas.router)
app.include_router(salud.router)
app.include_router(alertas.router)
