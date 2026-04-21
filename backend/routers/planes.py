from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Plan

router = APIRouter(prefix="/planes", tags=["Planes"])


@router.get("/")
def listar_planes(db: Session = Depends(get_db)):
    planes = db.query(Plan).filter(Plan.activo == True).all()
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "precio": p.precio,
            "duracion_dias": p.duracion_dias,
            "descripcion": p.descripcion,
        }
        for p in planes
    ]
