"""
Envío de mensajes por la WhatsApp Cloud API de Meta.

Único consumidor hoy: los recordatorios de vencimiento de membresía
(`enviar_pendientes` en routers/alertas.py, disparado por el job diario).

Degradación segura — mismo criterio que storage.py con S3: si faltan
WA_PHONE_NUMBER_ID / WA_ACCESS_TOKEN, o si WA_ENVIO_AUTOMATICO != "1",
HABILITADO queda en False y el sistema sigue funcionando en modo manual
(el botón de WhatsApp del panel del Resumen). Nada revienta por falta de
configuración: en dev y en los tests eso es lo normal.

**Ninguna función de este módulo levanta excepciones hacia el llamador.**
Todo error se devuelve en `Resultado`. El llamador es un job que recorre una
lista de socios; si reventara a la mitad dejaría media tanda sin enviar y sin
registro de por qué.

La ventana de 24 horas de WhatsApp: solo se puede mandar texto libre si el
cliente le escribió al negocio en las últimas 24 h. Los socios nunca escriben
primero, así que la ventana está siempre cerrada y el ÚNICO mensaje enviable
es una plantilla previamente aprobada por Meta (texto libre → error 131047).
Por eso acá solo hay envío de plantillas.

Variables de entorno:
  WA_PHONE_NUMBER_ID       ID del número emisor en la WABA (su presencia + el
                           token activan el envío automático)
  WA_ACCESS_TOKEN          system user token PERMANENTE. El token que muestra
                           el panel de "Getting Started" de Meta vence a las
                           24 h: funciona en la prueba y falla al día siguiente
  WA_TEMPLATE_VENCIMIENTO  nombre exacto de la plantilla aprobada
  WA_TEMPLATE_LANG         código de idioma de la plantilla. Debe coincidir
                           EXACTO con el que se eligió al crearla: "es" y
                           "es_CO" son distintos y el mismatch da error 132001
  WA_API_VERSION           versión de Graph API (default v21.0)
  WA_TIMEOUT               timeout HTTP en segundos
  WA_ENVIO_AUTOMATICO      "0" apaga el envío sin borrar las credenciales
  WA_DRY_RUN               "1" arma y loguea el payload sin llamar a Meta
  WA_MAX_POR_CORRIDA       tope de mensajes por ejecución del job
"""

import os
from dataclasses import dataclass
from typing import Optional

WA_PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID", "")
WA_ACCESS_TOKEN = os.getenv("WA_ACCESS_TOKEN", "")
WA_TEMPLATE_VENCIMIENTO = os.getenv("WA_TEMPLATE_VENCIMIENTO", "recordatorio_vencimiento")
WA_TEMPLATE_LANG = os.getenv("WA_TEMPLATE_LANG", "es")
WA_API_VERSION = os.getenv("WA_API_VERSION", "v21.0")
WA_TIMEOUT = float(os.getenv("WA_TIMEOUT", "10"))
WA_DRY_RUN = os.getenv("WA_DRY_RUN", "0") == "1"
WA_MAX_POR_CORRIDA = int(os.getenv("WA_MAX_POR_CORRIDA", "50"))

HABILITADO = (
    bool(WA_PHONE_NUMBER_ID and WA_ACCESS_TOKEN)
    and os.getenv("WA_ENVIO_AUTOMATICO", "1") == "1"
)

# Los mensajes de error se guardan en AlertaMembresia.error_envio, String(300).
MAX_ERROR = 300

_cliente_http = None


def _cliente():
    """Cliente httpx perezoso y cacheado (mismo patrón que _s3() en storage.py).

    Se usa el cliente SÍNCRONO a propósito: el llamador es un job de APScheduler
    que corre en su propio thread, no en el event loop de FastAPI. Los tests lo
    monkeypatchean para inyectar un httpx.MockTransport.
    """
    global _cliente_http
    if _cliente_http is None:
        import httpx
        _cliente_http = httpx.Client(timeout=WA_TIMEOUT)
    return _cliente_http


@dataclass
class Resultado:
    ok: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


def normalizar_telefono(t: Optional[str]) -> Optional[str]:
    """'57' + los últimos 10 dígitos. None si no hay al menos 10 dígitos.

    Espeja _telefono() de frontend/src/views/DashboardView.vue — mantener las
    dos en sincronía, si no el link manual y el automático le escribirían a
    números distintos. El prefijo de Colombia va fijo, igual que allá.
    """
    digitos = "".join(c for c in (t or "") if c.isdigit())
    if len(digitos) < 10:
        return None
    return "57" + digitos[-10:]


def enviar_recordatorio(telefono: str, nombre: str, cuando: str, fecha: str) -> Resultado:
    """Manda la plantilla de vencimiento. `telefono` ya normalizado.

    Los tres parámetros son posicionales y su orden es el de la plantilla
    aprobada en Meta ({{1}} nombre, {{2}} cuándo, {{3}} fecha). Cambiar el
    orden acá sin cambiarlo allá manda los datos cruzados sin ningún error.
    """
    if not HABILITADO:
        return Resultado(ok=False, error="WhatsApp API no configurada")

    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "template",
        "template": {
            "name": WA_TEMPLATE_VENCIMIENTO,
            "language": {"code": WA_TEMPLATE_LANG},
            "components": [{
                "type": "body",
                "parameters": [
                    {"type": "text", "text": nombre},
                    {"type": "text", "text": cuando},
                    {"type": "text", "text": fecha},
                ],
            }],
        },
    }

    if WA_DRY_RUN:
        print(f"[WhatsApp DRY_RUN] {payload}")
        return Resultado(ok=True, message_id="dry-run")

    url = f"https://graph.facebook.com/{WA_API_VERSION}/{WA_PHONE_NUMBER_ID}/messages"
    try:
        r = _cliente().post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {WA_ACCESS_TOKEN}"},
        )
        data = r.json() if r.content else {}
    except Exception as e:
        # Amplio a propósito: cubre timeout, DNS caído y el .json() de una
        # respuesta HTML de un proxy, con un solo camino de salida.
        return Resultado(ok=False, error=f"{type(e).__name__}: {e}"[:MAX_ERROR])

    if r.status_code >= 400:
        err = data.get("error") or {}
        return Resultado(
            ok=False,
            error=f"[{err.get('code')}] {err.get('message')}"[:MAX_ERROR],
        )

    mensajes = data.get("messages") or [{}]
    return Resultado(ok=True, message_id=mensajes[0].get("id"))
