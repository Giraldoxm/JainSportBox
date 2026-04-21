from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class WODCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    descripcion: str = Field(..., min_length=1)
    fecha: date


class WODUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=150)
    descripcion: Optional[str] = Field(None, min_length=1)
    fecha: Optional[date] = None


class WODResponse(BaseModel):
    id: int
    titulo: str
    descripcion: str
    fecha: date
    coach_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
