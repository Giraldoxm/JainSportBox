from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Asistencia, RolUsuario, Usuario
from schemas.asistencia import AsistenciaCreate, AsistenciaResponse
from security import get_current_user

router = APIRouter(prefix="/asistencia", tags=["Asistencia"])


def _require_admin_or_coach(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in (RolUsuario.ADMIN, RolUsuario.COACH):
        raise HTTPException(status_code=403, detail="Solo admin o coach pueden realizar esta acción.")
    return current_user


def _registrar(usuario: Usuario, db: Session) -> AsistenciaResponse:
    tipo = "salida" if usuario.esta_en_gym else "entrada"
    asistencia = Asistencia(usuario_id=usuario.id, tipo=tipo)
    db.add(asistencia)
    usuario.esta_en_gym = not usuario.esta_en_gym
    db.commit()
    db.refresh(asistencia)
    return AsistenciaResponse(
        id=asistencia.id,
        usuario_id=asistencia.usuario_id,
        tipo=asistencia.tipo,
        fecha_hora=asistencia.fecha_hora,
        nombre_usuario=usuario.nombre,
    )


@router.post("/", response_model=AsistenciaResponse, status_code=status.HTTP_201_CREATED)
def registrar_asistencia(payload: AsistenciaCreate, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.huella_id == payload.huella_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado con esa huella.")
    return _registrar(usuario, db)


@router.post("/por-usuario/{usuario_id}", response_model=AsistenciaResponse, status_code=status.HTTP_201_CREATED)
def registrar_asistencia_por_id(usuario_id: int, db: Session = Depends(get_db)):
    """
    Registra asistencia dado el usuario_id directamente.
    Usado por el bridge DigitalPersona después de identificar la huella localmente.
    Valida que la membresía esté vigente antes de permitir entrada.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Solo valida membresía en entradas, no en salidas
    if not usuario.esta_en_gym:
        if not usuario.fecha_vencimiento or usuario.fecha_vencimiento < date.today():
            raise HTTPException(
                status_code=403,
                detail=f"Membresía vencida o sin plan activo para {usuario.nombre}.",
            )

    return _registrar(usuario, db)


@router.get("/mi-historial")
def mi_historial(
    meses: int = Query(4, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    hoy = date.today()
    mes = hoy.month
    anio = hoy.year
    for _ in range(meses - 1):
        mes -= 1
        if mes == 0:
            mes = 12
            anio -= 1
    desde = datetime(anio, mes, 1)

    asistencias = (
        db.query(Asistencia)
        .filter(
            Asistencia.usuario_id == current_user.id,
            Asistencia.tipo == "entrada",
            Asistencia.fecha_hora >= desde,
        )
        .order_by(Asistencia.fecha_hora)
        .all()
    )

    fechas = sorted(set(a.fecha_hora.date().isoformat() for a in asistencias))
    return {"fechas": fechas, "total": len(fechas)}


@router.get("/historial/{usuario_id}")
def historial_usuario(
    usuario_id: int,
    meses: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    hoy = date.today()
    mes = hoy.month
    anio = hoy.year
    for _ in range(meses - 1):
        mes -= 1
        if mes == 0:
            mes = 12
            anio -= 1
    desde = datetime(anio, mes, 1)

    asistencias = (
        db.query(Asistencia)
        .filter(
            Asistencia.usuario_id == usuario_id,
            Asistencia.tipo == "entrada",
            Asistencia.fecha_hora >= desde,
        )
        .order_by(Asistencia.fecha_hora)
        .all()
    )

    fechas = sorted(set(a.fecha_hora.date().isoformat() for a in asistencias))
    return {"fechas": fechas, "total": len(fechas)}
