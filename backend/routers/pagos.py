from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Pago, Plan, Usuario
from schemas.pago import PagoCreate, PagoResponse

router = APIRouter(prefix="/pagos", tags=["Planes"])


@router.post("/", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
def registrar_pago(payload: PagoCreate, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == payload.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    plan = db.query(Plan).filter(Plan.id == payload.plan_id, Plan.activo == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado o inactivo.")

    pago = Pago(
        usuario_id=payload.usuario_id,
        plan_id=payload.plan_id,
        monto=payload.monto,
        metodo_pago=payload.metodo_pago,
    )
    db.add(pago)

    hoy = date.today()
    base = (
        usuario.fecha_vencimiento
        if (usuario.fecha_vencimiento and usuario.fecha_vencimiento >= hoy)
        else hoy
    )
    nueva_fecha = base + timedelta(days=plan.duracion_dias)
    usuario.fecha_vencimiento = nueva_fecha

    db.commit()
    db.refresh(pago)

    return PagoResponse(
        id=pago.id,
        usuario_id=pago.usuario_id,
        plan_id=pago.plan_id,
        fecha_pago=pago.fecha_pago,
        monto=pago.monto,
        metodo_pago=pago.metodo_pago,
        nueva_fecha_vencimiento=nueva_fecha,
    )


class PagoDirectoCreate(BaseModel):
    usuario_id: int
    duracion_dias: int = Field(..., ge=1, le=365)
    monto: float = Field(..., gt=0)
    metodo_pago: Optional[str] = None


@router.post("/directo/", status_code=status.HTTP_201_CREATED, tags=["Planes"])
def registrar_pago_directo(payload: PagoDirectoCreate, db: Session = Depends(get_db)):
    """Asigna un plan personalizado (días libres) sin requerir plan_id."""
    usuario = db.query(Usuario).filter(Usuario.id == payload.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    hoy = date.today()
    base = (
        usuario.fecha_vencimiento
        if (usuario.fecha_vencimiento and usuario.fecha_vencimiento >= hoy)
        else hoy
    )
    nueva_fecha = base + timedelta(days=payload.duracion_dias)
    usuario.fecha_vencimiento = nueva_fecha

    db.commit()

    return {
        "usuario_id": usuario.id,
        "duracion_dias": payload.duracion_dias,
        "monto": payload.monto,
        "nueva_fecha_vencimiento": nueva_fecha,
    }
