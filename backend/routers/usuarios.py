import shutil
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import MovimientoFinanciero, Pago, Plan, RolUsuario, TipoMovimiento, Usuario
from schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from security import get_current_user, get_password_hash

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def _require_admin_or_coach(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in (RolUsuario.ADMIN, RolUsuario.COACH):
        raise HTTPException(status_code=403, detail="Solo admin o coach pueden realizar esta acción.")
    return current_user


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    if db.query(Usuario).filter(Usuario.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email.")
    if db.query(Usuario).filter(Usuario.documento_identidad == payload.documento_identidad).first():
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese documento de identidad.")
    nuevo = Usuario(
        nombre=payload.nombre,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        documento_identidad=payload.documento_identidad,
        genero=payload.genero,
        rol=payload.rol,
        huella_id=payload.huella_id,
        telefono=payload.telefono,
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
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if payload.nombre is not None:
        usuario.nombre = payload.nombre

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

    if payload.telefono is not None:
        usuario.telefono = payload.telefono

    if payload.documento_identidad is not None:
        duplicado_doc = (
            db.query(Usuario)
            .filter(Usuario.documento_identidad == payload.documento_identidad, Usuario.id != usuario_id)
            .first()
        )
        if duplicado_doc:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese documento de identidad.")
        usuario.documento_identidad = payload.documento_identidad

    if payload.genero is not None:
        usuario.genero = payload.genero

    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/{usuario_id}/foto", response_model=UsuarioResponse)
def subir_foto(
    usuario_id: int,
    foto: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
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
    current_user: Usuario = Depends(_require_admin_or_coach),
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


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return usuario


@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    return db.query(Usuario).filter(Usuario.rol != RolUsuario.PENDIENTE).all()


@router.get("/pendientes")
def listar_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    pendientes = db.query(Usuario).filter(Usuario.rol == RolUsuario.PENDIENTE).all()
    result = []
    for u in pendientes:
        plan_solicitado = None
        if u.plan_solicitado_id:
            p = db.query(Plan).filter(Plan.id == u.plan_solicitado_id).first()
            if p:
                plan_solicitado = {"id": p.id, "nombre": p.nombre, "precio": p.precio, "duracion_dias": p.duracion_dias}
        result.append({
            "id": u.id,
            "nombre": u.nombre,
            "email": u.email,
            "documento_identidad": u.documento_identidad,
            "genero": u.genero,
            "created_at": u.created_at,
            "plan_solicitado_id": u.plan_solicitado_id,
            "plan_solicitado": plan_solicitado,
        })
    return result


class ActivarUsuarioPayload(BaseModel):
    plan_id: int
    monto: float = Field(..., ge=0)
    metodo_pago: str = Field(..., pattern=r'^(efectivo|transferencia)$')


@router.post("/{usuario_id}/activar")
def activar_usuario(
    usuario_id: int,
    payload: ActivarUsuarioPayload,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id, Usuario.rol == RolUsuario.PENDIENTE).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario pendiente no encontrado.")

    plan = db.query(Plan).filter(Plan.id == payload.plan_id, Plan.activo == True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado.")

    usuario.rol = RolUsuario.CLIENTE
    usuario.plan_solicitado_id = None
    nueva_fecha = date.today() + timedelta(days=plan.duracion_dias)
    usuario.fecha_vencimiento = nueva_fecha

    pago = Pago(
        usuario_id=usuario.id,
        plan_id=plan.id,
        monto=payload.monto,
        metodo_pago=payload.metodo_pago,
    )
    db.add(pago)

    if payload.monto > 0:
        mov = MovimientoFinanciero(
            tipo=TipoMovimiento.INGRESO,
            concepto=f"Activación de cuenta – {usuario.nombre} ({plan.nombre})",
            categoria="mensualidad",
            monto=payload.monto,
            fecha=datetime.utcnow(),
            metodo_pago=payload.metodo_pago,
            usuario_id=usuario.id,
            fuente="pago_membresia",
            created_by=current_user.id,
        )
        db.add(mov)

    db.commit()
    return {
        "message": f"Usuario {usuario.nombre} activado correctamente.",
        "usuario_id": usuario.id,
        "nueva_fecha_vencimiento": nueva_fecha,
    }


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


class HuellaTemplatePayload(BaseModel):
    template: str  # base64-encoded FMD


@router.post("/{usuario_id}/huella-template", status_code=status.HTTP_200_OK)
def guardar_huella_template(
    usuario_id: int,
    payload: HuellaTemplatePayload,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    """Guarda el template de huella (base64 FMD) para un usuario. Llamado por el bridge."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    usuario.huella_template = payload.template
    usuario.huella_id = f"dp_{usuario_id}"
    db.commit()
    return {"mensaje": f"Huella registrada para {usuario.nombre}."}


@router.get("/con-template/lista")
def listar_usuarios_con_template(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    """Devuelve id, nombre y template de todos los usuarios con huella registrada. Usado por el bridge."""
    usuarios = (
        db.query(Usuario.id, Usuario.nombre, Usuario.huella_template)
        .filter(Usuario.huella_template.isnot(None))
        .all()
    )
    return [
        {"id": u.id, "nombre": u.nombre, "template": u.huella_template}
        for u in usuarios
    ]
