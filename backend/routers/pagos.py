from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import MovimientoFinanciero, Pago, Plan, RolUsuario, TipoMovimiento, Usuario
from schemas.pago import PagoCreate, PagoResponse
from security import get_current_user

router = APIRouter(prefix="/pagos", tags=["Planes"])


def _require_admin_or_coach(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in (RolUsuario.ADMIN, RolUsuario.COACH):
        raise HTTPException(status_code=403, detail="Solo admin o coach pueden realizar esta acción.")
    return current_user


@router.post("/", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
def registrar_pago(
    payload: PagoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
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
    monto: float = Field(..., ge=0)
    metodo_pago: str = Field(..., pattern=r'^(efectivo|transferencia)$')


@router.post("/directo/", status_code=status.HTTP_201_CREATED)
def registrar_pago_directo(
    payload: PagoDirectoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
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

    if payload.monto > 0:
        mov = MovimientoFinanciero(
            tipo=TipoMovimiento.INGRESO,
            concepto=f"Membresía personalizada – {usuario.nombre} ({payload.duracion_dias} días)",
            categoria="mensualidad",
            monto=payload.monto,
            fecha=datetime.utcnow(),
            metodo_pago=payload.metodo_pago,
            usuario_id=usuario.id,
            fuente="pago_directo",
            created_by=current_user.id,
        )
        db.add(mov)

    db.commit()

    return {
        "usuario_id": usuario.id,
        "duracion_dias": payload.duracion_dias,
        "monto": payload.monto,
        "nueva_fecha_vencimiento": nueva_fecha,
    }


@router.get("/usuario/{usuario_id}")
def historial_pagos(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    pagos = (
        db.query(Pago)
        .filter(Pago.usuario_id == usuario_id)
        .order_by(Pago.fecha_pago.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "plan_id": p.plan_id,
            "plan_nombre": p.plan.nombre if p.plan else "Personalizado",
            "fecha_pago": p.fecha_pago,
            "monto": p.monto,
            "metodo_pago": p.metodo_pago,
        }
        for p in pagos
    ]
