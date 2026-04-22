from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import RolUsuario, Usuario, WOD
from schemas.wod import WODCreate, WODUpdate, WODResponse
from security import get_current_user

router = APIRouter(prefix="/wods", tags=["WODs"])


def _require_admin_or_coach(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in (RolUsuario.ADMIN, RolUsuario.COACH):
        raise HTTPException(status_code=403, detail="Solo admin o coach pueden realizar esta acción.")
    return current_user


@router.post("/", response_model=WODResponse, status_code=status.HTTP_201_CREATED)
def crear_wod(
    payload: WODCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    data = payload.model_dump()
    data["coach_id"] = current_user.id
    wod = WOD(**data)
    db.add(wod)
    db.commit()
    db.refresh(wod)
    return wod


@router.put("/{wod_id}", response_model=WODResponse)
def actualizar_wod(
    wod_id: int,
    payload: WODUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    wod = db.query(WOD).filter(WOD.id == wod_id).first()
    if not wod:
        raise HTTPException(status_code=404, detail="WOD no encontrado.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(wod, field, value)
    db.commit()
    db.refresh(wod)
    return wod


@router.patch("/{wod_id}/toggle", response_model=WODResponse)
def toggle_wod(
    wod_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    wod = db.query(WOD).filter(WOD.id == wod_id).first()
    if not wod:
        raise HTTPException(status_code=404, detail="WOD no encontrado.")
    wod.activo = not wod.activo
    db.commit()
    db.refresh(wod)
    return wod


@router.delete("/{wod_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_wod(
    wod_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    wod = db.query(WOD).filter(WOD.id == wod_id).first()
    if not wod:
        raise HTTPException(status_code=404, detail="WOD no encontrado.")
    db.delete(wod)
    db.commit()


@router.get("/hoy", response_model=List[WODResponse])
def wods_de_hoy(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    es_staff = current_user.rol in (RolUsuario.ADMIN, RolUsuario.COACH)
    q = db.query(WOD).filter(WOD.fecha == date.today())
    if not es_staff:
        q = q.filter(WOD.activo == True)
    return q.order_by(WOD.id).all()


@router.get("/", response_model=List[WODResponse])
def listar_wods(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    es_staff = current_user.rol in (RolUsuario.ADMIN, RolUsuario.COACH)
    q = db.query(WOD)
    if not es_staff:
        q = q.filter(WOD.activo == True)
    return q.order_by(WOD.fecha.desc(), WOD.id.desc()).limit(limit).all()
