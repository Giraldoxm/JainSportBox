from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import RolUsuario, Usuario, WOD
from schemas.wod import WODCreate, WODResponse

router = APIRouter(prefix="/wods", tags=["WODs"])


@router.post("/", response_model=WODResponse, status_code=status.HTTP_201_CREATED)
def crear_wod(payload: WODCreate, db: Session = Depends(get_db)):
    if db.query(WOD).filter(WOD.fecha == payload.fecha).first():
        raise HTTPException(status_code=400, detail=f"Ya existe un WOD para la fecha {payload.fecha}.")
    if payload.coach_id:
        coach = db.query(Usuario).filter(
            Usuario.id == payload.coach_id,
            Usuario.rol == RolUsuario.COACH,
        ).first()
        if not coach:
            raise HTTPException(status_code=404, detail="Coach no encontrado o el usuario no tiene rol de Coach.")
    wod = WOD(**payload.model_dump())
    db.add(wod)
    db.commit()
    db.refresh(wod)
    return wod


@router.get("/hoy", response_model=WODResponse)
def wod_de_hoy(db: Session = Depends(get_db)):
    wod = db.query(WOD).filter(WOD.fecha == date.today()).first()
    if not wod:
        raise HTTPException(status_code=404, detail="No hay WOD programado para hoy.")
    return wod


@router.get("/", response_model=List[WODResponse])
def listar_wods(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return db.query(WOD).order_by(WOD.fecha.desc()).limit(limit).all()
