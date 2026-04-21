from datetime import datetime

from pydantic import BaseModel


class AsistenciaCreate(BaseModel):
    huella_id: str


class AsistenciaResponse(BaseModel):
    id: int
    usuario_id: int
    tipo: str
    fecha_hora: datetime
    nombre_usuario: str = ""

    model_config = {"from_attributes": True}
