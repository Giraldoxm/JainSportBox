"""§11 — Módulo de envío por WhatsApp Cloud API (backend/whatsapp.py).

Los tests van contra httpx.MockTransport, NO monkeypatcheando
`enviar_recordatorio`: mockear la función bajo prueba no probaría nada. Con el
transporte falso se ejercita el armado del payload, los headers y el parseo de
la respuesta, y cualquier intento de salir a internet de verdad falla ruidoso.
"""

import httpx
import pytest

import whatsapp


@pytest.fixture
def wa_mock(monkeypatch):
    """Habilita el módulo e inyecta un transporte falso.

    Devuelve una función que recibe el handler de respuesta y entrega la lista
    de requests capturados, para poder afirmar sobre el payload enviado.
    """

    def _armar(handler):
        capturados = []

        def _handler(request):
            capturados.append(request)
            return handler(request)

        monkeypatch.setattr(whatsapp, "HABILITADO", True)
        monkeypatch.setattr(whatsapp, "WA_PHONE_NUMBER_ID", "1234567890")
        monkeypatch.setattr(whatsapp, "WA_ACCESS_TOKEN", "token-de-prueba")
        monkeypatch.setattr(whatsapp, "WA_DRY_RUN", False)
        monkeypatch.setattr(
            whatsapp,
            "_cliente",
            lambda: httpx.Client(transport=httpx.MockTransport(_handler)),
        )
        return capturados

    return _armar


def _ok(payload=None):
    cuerpo = payload or {"messages": [{"id": "wamid.ABC123"}]}
    return lambda request: httpx.Response(200, json=cuerpo)


# ── 11.1 / 11.2 · normalizar_telefono ────────────────────────────────


@pytest.mark.parametrize("entrada", [
    "300 123 4567",
    "+57 300 1234567",
    "3001234567",
    "57 300 123 45 67",
    "(300) 123-4567",
])
def test_normalizar_telefono_variantes_dan_el_mismo_numero(entrada):
    assert whatsapp.normalizar_telefono(entrada) == "573001234567"


@pytest.mark.parametrize("entrada", [None, "", "   ", "123", "sin numero"])
def test_normalizar_telefono_descarta_lo_inservible(entrada):
    assert whatsapp.normalizar_telefono(entrada) is None


# ── 11.3 · payload y headers ─────────────────────────────────────────


def test_payload_respeta_el_contrato_de_la_cloud_api(wa_mock):
    capturados = wa_mock(_ok())

    whatsapp.enviar_recordatorio("573001234567", "Camila", "en 3 días", "15/08/2026")

    assert len(capturados) == 1
    req = capturados[0]

    assert "1234567890/messages" in str(req.url)
    assert req.headers["Authorization"] == "Bearer token-de-prueba"

    import json
    body = json.loads(req.content)
    assert body["messaging_product"] == "whatsapp"
    assert body["to"] == "573001234567"
    assert body["type"] == "template"
    assert body["template"]["name"] == whatsapp.WA_TEMPLATE_VENCIMIENTO
    assert body["template"]["language"]["code"] == whatsapp.WA_TEMPLATE_LANG

    # El orden es el de la plantilla aprobada en Meta: {{1}} {{2}} {{3}}.
    # Cruzarlo no da error, solo manda el mensaje mal.
    params = body["template"]["components"][0]["parameters"]
    assert [p["text"] for p in params] == ["Camila", "en 3 días", "15/08/2026"]


# ── 11.4 a 11.7 · resultados ─────────────────────────────────────────


def test_respuesta_ok_devuelve_el_message_id(wa_mock):
    wa_mock(_ok())
    r = whatsapp.enviar_recordatorio("573001234567", "Camila", "hoy", "15/08/2026")
    assert r.ok is True
    assert r.message_id == "wamid.ABC123"
    assert r.error is None


def test_error_de_meta_no_lanza_y_conserva_el_codigo(wa_mock):
    wa_mock(lambda request: httpx.Response(400, json={
        "error": {"code": 131026, "message": "Message undeliverable"}
    }))

    r = whatsapp.enviar_recordatorio("573001234567", "Camila", "hoy", "15/08/2026")

    assert r.ok is False
    assert "131026" in r.error
    assert "undeliverable" in r.error.lower()


def test_error_de_red_no_lanza(wa_mock):
    def _revienta(request):
        raise httpx.ConnectTimeout("timeout simulado")

    wa_mock(_revienta)

    r = whatsapp.enviar_recordatorio("573001234567", "Camila", "hoy", "15/08/2026")

    assert r.ok is False
    assert "ConnectTimeout" in r.error


def test_error_se_trunca_para_caber_en_la_columna(wa_mock):
    wa_mock(lambda request: httpx.Response(400, json={
        "error": {"code": 1, "message": "x" * 1000}
    }))

    r = whatsapp.enviar_recordatorio("573001234567", "Camila", "hoy", "15/08/2026")

    assert len(r.error) <= whatsapp.MAX_ERROR


def test_sin_credenciales_no_se_intenta_la_llamada(monkeypatch):
    """Degradación segura: es el estado por defecto de toda la suite."""
    llamado = []
    monkeypatch.setattr(whatsapp, "HABILITADO", False)
    monkeypatch.setattr(
        whatsapp, "_cliente",
        lambda: llamado.append(1) or pytest.fail("no debería construirse el cliente"),
    )

    r = whatsapp.enviar_recordatorio("573001234567", "Camila", "hoy", "15/08/2026")

    assert r.ok is False
    assert "no configurada" in r.error
    assert llamado == []


def test_dry_run_no_sale_a_la_red(wa_mock, monkeypatch):
    capturados = wa_mock(_ok())
    monkeypatch.setattr(whatsapp, "WA_DRY_RUN", True)

    r = whatsapp.enviar_recordatorio("573001234567", "Camila", "hoy", "15/08/2026")

    assert r.ok is True
    assert r.message_id == "dry-run"
    assert capturados == []
