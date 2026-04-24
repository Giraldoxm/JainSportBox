import math
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import MarcaRM, Usuario
from schemas.marcas import MarcaRMCreate, MarcaRMResponse
from security import get_current_user

router = APIRouter(prefix="/marcas", tags=["Marcas RM"])


def _calcular_1rm(peso: float, reps: int) -> float:
    w, r = peso, reps
    valores = [
        w * (36 / (37 - r)),                                    # Brzycki
        w * (1 + r / 30),                                        # Epley
        (100 * w) / (101.3 - 2.67123 * r),                     # Lander
        w * (1 + 0.025 * r),                                     # O'Conner
        w * (r ** 0.1),                                          # Lombardi
        (100 * w) / (52.2 + 41.9 * math.exp(-0.055 * r)),      # Mayhew
        (100 * w) / (48.8 + 53.8 * math.exp(-0.075 * r)),      # Wathen
    ]
    return round(sum(valores) / len(valores), 2)


@router.get("/", response_model=List[MarcaRMResponse])
def listar_todas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return (
        db.query(MarcaRM)
        .filter(MarcaRM.usuario_id == current_user.id)
        .order_by(MarcaRM.fecha.asc())
        .all()
    )


@router.get("/{ejercicio}", response_model=List[MarcaRMResponse])
def listar_por_ejercicio(
    ejercicio: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return (
        db.query(MarcaRM)
        .filter(MarcaRM.usuario_id == current_user.id, MarcaRM.ejercicio == ejercicio)
        .order_by(MarcaRM.fecha.asc())
        .all()
    )


@router.post("/", response_model=MarcaRMResponse, status_code=status.HTTP_201_CREATED)
def crear_marca(
    payload: MarcaRMCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    rm = _calcular_1rm(payload.peso, payload.repeticiones)
    marca = MarcaRM(
        usuario_id=current_user.id,
        ejercicio=payload.ejercicio.strip(),
        peso=payload.peso,
        unidad=payload.unidad,
        repeticiones=payload.repeticiones,
        rm_calculado=rm,
        fecha=payload.fecha,
        notas=payload.notas,
    )
    db.add(marca)
    db.commit()
    db.refresh(marca)
    return marca


@router.delete("/{marca_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_marca(
    marca_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    marca = db.query(MarcaRM).filter(
        MarcaRM.id == marca_id,
        MarcaRM.usuario_id == current_user.id,
    ).first()
    if not marca:
        raise HTTPException(status_code=404, detail="Marca no encontrada.")
    db.delete(marca)
    db.commit()
