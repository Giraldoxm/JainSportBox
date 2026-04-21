from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from models import RolUsuario


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., max_length=120)
    password: str = Field(..., min_length=6)
    rol: RolUsuario = RolUsuario.CLIENTE
    huella_id: Optional[str] = None


class UsuarioUpdate(BaseModel):
    email: Optional[str] = Field(None, max_length=120)
    password: Optional[str] = Field(None, min_length=6)


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: RolUsuario
    huella_id: Optional[str]
    fecha_vencimiento: Optional[date]
    esta_en_gym: bool
    foto_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
