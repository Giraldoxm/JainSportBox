from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Producto, Usuario, Venta
from schemas.venta import VentaCreate, VentaResponse
from security import get_current_user

router = APIRouter(prefix="/ventas", tags=["Ventas"])


@router.post("/", response_model=VentaResponse, status_code=status.HTTP_201_CREATED)
def registrar_venta(
    payload: VentaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    producto = db.query(Producto).filter(Producto.id == payload.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    if not producto.activo:
        raise HTTPException(status_code=400, detail="El producto no esta activo.")
    if producto.stock < payload.cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Disponible: {producto.stock}, solicitado: {payload.cantidad}.",
        )
    if payload.usuario_id and not db.query(Usuario).filter(Usuario.id == payload.usuario_id).first():
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    venta = Venta(
        producto_id=payload.producto_id,
        usuario_id=payload.usuario_id,
        cantidad=payload.cantidad,
        precio_unitario=producto.precio,
        total=producto.precio * payload.cantidad,
    )
    db.add(venta)
    producto.stock -= payload.cantidad
    db.commit()
    db.refresh(venta)
    return venta


@router.get("/", response_model=List[VentaResponse])
def listar_ventas(db: Session = Depends(get_db)):
    return db.query(Venta).order_by(Venta.fecha_venta.desc()).all()
