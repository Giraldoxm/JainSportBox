import models
from database import engine

models.Base.metadata.create_all(bind=engine)

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import asistencia, auth, pagos, planes, productos, usuarios, ventas, wods

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
