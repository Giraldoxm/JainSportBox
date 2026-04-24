from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Asistencia, Usuario
from schemas.asistencia import AsistenciaCreate, AsistenciaResponse

router = APIRouter(prefix="/asistencia", tags=["Asistencia"])


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
