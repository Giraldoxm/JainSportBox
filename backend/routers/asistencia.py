from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Asistencia, Usuario
from schemas.asistencia import AsistenciaCreate, AsistenciaResponse

router = APIRouter(prefix="/asistencia", tags=["Asistencia"])


@router.post("/", response_model=AsistenciaResponse, status_code=status.HTTP_201_CREATED)
def registrar_asistencia(payload: AsistenciaCreate, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.huella_id == payload.huella_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado con esa huella.")

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
