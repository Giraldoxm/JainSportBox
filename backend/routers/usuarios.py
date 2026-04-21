import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario
from schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from security import get_current_user, get_password_hash

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email.")
    nuevo = Usuario(
        nombre=payload.nombre,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        rol=payload.rol,
        huella_id=payload.huella_id,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if payload.email is not None:
        duplicado = (
            db.query(Usuario)
            .filter(Usuario.email == payload.email, Usuario.id != usuario_id)
            .first()
        )
        if duplicado:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email.")
        usuario.email = payload.email

    if payload.password is not None:
        usuario.password_hash = get_password_hash(payload.password)

    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/{usuario_id}/foto", response_model=UsuarioResponse)
def subir_foto(
    usuario_id: int,
    foto: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if foto.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Formato no permitido. Usa JPG, PNG o WEBP.")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if usuario.foto_url:
        archivo_anterior = UPLOADS_DIR / Path(usuario.foto_url).name
        if archivo_anterior.exists():
            archivo_anterior.unlink()

    extension = foto.filename.rsplit(".", 1)[-1].lower()
    nombre_archivo = f"{uuid.uuid4().hex}.{extension}"
    destino = UPLOADS_DIR / nombre_archivo

    with destino.open("wb") as f:
        shutil.copyfileobj(foto.file, f)

    usuario.foto_url = f"/uploads/{nombre_archivo}"
    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if usuario.foto_url:
        archivo = UPLOADS_DIR / Path(usuario.foto_url).name
        if archivo.exists():
            archivo.unlink()
    db.delete(usuario)
    db.commit()


@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return db.query(Usuario).all()


@router.get("/huella/{huella_id}", response_model=UsuarioResponse)
def buscar_por_huella(
    huella_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    usuario = db.query(Usuario).filter(Usuario.huella_id == huella_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado con esa huella.")
    return usuario
