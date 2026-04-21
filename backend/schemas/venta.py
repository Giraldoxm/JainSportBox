from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VentaCreate(BaseModel):
    producto_id: int
    usuario_id: Optional[int] = None
    cantidad: int = Field(1, ge=1)


class VentaResponse(BaseModel):
    id: int
    producto_id: int
    usuario_id: Optional[int]
    cantidad: int
    precio_unitario: float
    total: float
    fecha_venta: datetime

    model_config = {"from_attributes": True}
