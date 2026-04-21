from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Producto, Usuario
from schemas.producto import ProductoCreate, ProductoResponse, ProductoUpdate
from security import get_current_user

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.get("/", response_model=List[ProductoResponse])
def listar_productos(
    solo_activos: bool = Query(True, description="Filtrar solo productos activos"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(Producto)
    if solo_activos:
        query = query.filter(Producto.activo == True)
    return query.all()


@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return producto


@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def crear_producto(
    payload: ProductoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    nuevo = Producto(**payload.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.put("/{producto_id}", response_model=ProductoResponse)
def editar_producto(
    producto_id: int,
    payload: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(producto, campo, valor)
    db.commit()
    db.refresh(producto)
    return producto
