from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class MarcaRMCreate(BaseModel):
    ejercicio: str = Field(..., min_length=1, max_length=100)
    peso: float = Field(..., gt=0)
    unidad: str = Field("kg", pattern="^(kg|lbs)$")
    repeticiones: int = Field(..., ge=1, le=36)
    fecha: date
    notas: Optional[str] = None


class MarcaRMResponse(BaseModel):
    id: int
    usuario_id: int
    ejercicio: str
    peso: float
    unidad: str
    repeticiones: int
    rm_calculado: float
    fecha: date
    notas: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
