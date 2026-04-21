import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from models import Producto, RolUsuario, Usuario
from schemas.producto import ProductoCreate, ProductoResponse, ProductoUpdate
from security import get_current_user

UPLOADS_DIR = Path(__file__).parent.parent / "uploads" / "productos"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

router = APIRouter(prefix="/productos", tags=["Productos"])


def _require_admin_or_coach(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in (RolUsuario.ADMIN, RolUsuario.COACH):
        raise HTTPException(status_code=403, detail="Solo admin o coach pueden realizar esta acción.")
    return current_user


@router.get("/", response_model=List[ProductoResponse])
def listar_productos(
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Clientes solo ven activos, admin/coach pueden ver todos
    if current_user.rol == RolUsuario.CLIENTE:
        solo_activos = True
    q = db.query(Producto)
    if solo_activos:
        q = q.filter(Producto.activo == True)
    return q.order_by(Producto.nombre).all()


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
    current_user: Usuario = Depends(_require_admin_or_coach),
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
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(producto, campo, valor)
    db.commit()
    db.refresh(producto)
    return producto


@router.post("/{producto_id}/foto", response_model=ProductoResponse)
def subir_foto(
    producto_id: int,
    foto: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    if foto.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Formato no permitido. Usa JPG, PNG o WEBP.")
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    if producto.foto_url:
        archivo_anterior = Path(__file__).parent.parent / producto.foto_url.lstrip("/")
        if archivo_anterior.exists():
            archivo_anterior.unlink()

    ext = foto.filename.rsplit(".", 1)[-1].lower()
    nombre_archivo = f"{uuid.uuid4().hex}.{ext}"
    destino = UPLOADS_DIR / nombre_archivo

    with destino.open("wb") as f:
        shutil.copyfileobj(foto.file, f)

    producto.foto_url = f"/uploads/productos/{nombre_archivo}"
    db.commit()
    db.refresh(producto)
    return producto


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(
    producto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    # Soft delete para preservar historial de ventas
    producto.activo = False
    db.commit()
