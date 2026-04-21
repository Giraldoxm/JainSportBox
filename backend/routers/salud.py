from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import MedidaSalud, Usuario
from schemas.salud import MedidaCreate, MedidaResponse
from security import get_current_user

router = APIRouter(prefix="/salud", tags=["Salud"])


def _calcular_imc(peso_kg: float, altura_cm: float) -> float:
    altura_m = altura_cm / 100
    return round(peso_kg / (altura_m ** 2), 2)


@router.get("/", response_model=List[MedidaResponse])
def listar_medidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return (
        db.query(MedidaSalud)
        .filter(MedidaSalud.usuario_id == current_user.id)
        .order_by(MedidaSalud.fecha.asc())
        .all()
    )


@router.post("/", response_model=MedidaResponse, status_code=status.HTTP_201_CREATED)
def crear_medida(
    payload: MedidaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    imc = _calcular_imc(payload.peso_kg, payload.altura_cm)
    medida = MedidaSalud(
        usuario_id=current_user.id,
        fecha=payload.fecha,
        peso_kg=payload.peso_kg,
        altura_cm=payload.altura_cm,
        imc=imc,
        cintura_cm=payload.cintura_cm,
        notas=payload.notas,
    )
    db.add(medida)
    db.commit()
    db.refresh(medida)
    return medida


@router.delete("/{medida_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_medida(
    medida_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    medida = db.query(MedidaSalud).filter(
        MedidaSalud.id == medida_id,
        MedidaSalud.usuario_id == current_user.id,
    ).first()
    if not medida:
        raise HTTPException(status_code=404, detail="Registro no encontrado.")
    db.delete(medida)
    db.commit()
