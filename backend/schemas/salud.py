from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class MedidaCreate(BaseModel):
    fecha: date
    peso_kg: float = Field(..., gt=0, le=500)
    altura_cm: float = Field(..., gt=0, le=300)
    cintura_cm: Optional[float] = Field(None, gt=0, le=300)
    notas: Optional[str] = None


class MedidaResponse(BaseModel):
    id: int
    usuario_id: int
    fecha: date
    peso_kg: float
    altura_cm: float
    imc: float
    cintura_cm: Optional[float]
    notas: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
