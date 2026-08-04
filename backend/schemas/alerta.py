from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class AlertaResponse(BaseModel):
    id: int
    usuario_id: int
    usuario_nombre: str
    usuario_telefono: Optional[str]
    fecha_vencimiento: date
    dias_anticipacion: int
    enviada: bool
    fecha_creacion: datetime
    fecha_enviada: Optional[datetime]
    # El panel los usa para los chips de canal y de falla de envío.
    # `intentos` y `wa_message_id` NO se exponen: son diagnóstico de servidor.
    canal: Optional[str] = None
    error_envio: Optional[str] = None

    model_config = {"from_attributes": True}
