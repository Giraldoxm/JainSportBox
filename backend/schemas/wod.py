from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class WODCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    descripcion: str = Field(..., min_length=1)
    fecha: date
    activo: bool = True
    es_personalizado: bool = False
    genero_destino: Optional[str] = Field(None, pattern=r'^(masculino|femenino)$')


class WODUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=150)
    descripcion: Optional[str] = Field(None, min_length=1)
    fecha: Optional[date] = None
    activo: Optional[bool] = None
    es_personalizado: Optional[bool] = None
    genero_destino: Optional[str] = Field(None, pattern=r'^(masculino|femenino)$')


class WODResponse(BaseModel):
    id: int
    titulo: str
    descripcion: str
    fecha: date
    activo: bool
    coach_id: Optional[int]
    es_personalizado: bool
    genero_destino: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
