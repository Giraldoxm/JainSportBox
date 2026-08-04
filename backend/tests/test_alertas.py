"""§10 de tests.md — Alertas de membresía: generación, dedup, renovación y
envío automático por WhatsApp."""

from datetime import date, datetime, timedelta

import httpx
import pytest

import models
import whatsapp


def _generar(client, headers):
    return client.post("/alertas/generar", headers=headers)


def _pendientes_de(db_session, usuario_id):
    return (
        db_session.query(models.AlertaMembresia)
        .filter_by(usuario_id=usuario_id, enviada=False)
        .all()
    )


def test_genera_alerta_dentro_de_ventana(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=3))
    r = _generar(client, admin_headers)
    assert r.status_code == 200
    alertas = _pendientes_de(db_session, actor.user.id)
    assert len(alertas) == 1
    assert alertas[0].dias_anticipacion == 3


def test_no_genera_fuera_de_ventana(client, admin_headers, crear_usuario, db_session):
    lejos = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=20))
    vencido = crear_usuario("cliente", fecha_vencimiento=date.today() - timedelta(days=1))
    _generar(client, admin_headers)
    assert _pendientes_de(db_session, lejos.user.id) == []
    assert _pendientes_de(db_session, vencido.user.id) == []


def test_generar_dos_veces_no_duplica(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=5))
    _generar(client, admin_headers)
    _generar(client, admin_headers)
    assert len(_pendientes_de(db_session, actor.user.id)) == 1


def test_renovacion_descarta_pendiente_obsoleta(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    _generar(client, admin_headers)
    assert len(_pendientes_de(db_session, actor.user.id)) == 1

    # renueva: nueva fecha fuera de la ventana de 7 días
    db_session.query(models.Usuario).filter_by(id=actor.user.id).update(
        {"fecha_vencimiento": date.today() + timedelta(days=32)}
    )
    db_session.commit()
    _generar(client, admin_headers)
    assert _pendientes_de(db_session, actor.user.id) == []


def test_renovacion_dentro_de_ventana_recrea(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=1))
    _generar(client, admin_headers)

    db_session.query(models.Usuario).filter_by(id=actor.user.id).update(
        {"fecha_vencimiento": date.today() + timedelta(days=6)}
    )
    db_session.commit()
    _generar(client, admin_headers)

    alertas = _pendientes_de(db_session, actor.user.id)
    assert len(alertas) == 1
    assert alertas[0].dias_anticipacion == 6
    assert alertas[0].fecha_vencimiento == date.today() + timedelta(days=6)


def test_marcar_enviada_y_listados(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=4))
    _generar(client, admin_headers)
    alerta = _pendientes_de(db_session, actor.user.id)[0]

    r = client.post(f"/alertas/{alerta.id}/marcar-enviada", headers=admin_headers)
    assert r.status_code == 200

    pendientes = client.get("/alertas/", headers=admin_headers).json()
    assert alerta.id not in [a["id"] for a in pendientes]
    todas = client.get("/alertas/?solo_pendientes=false", headers=admin_headers).json()
    enviada = next(a for a in todas if a["id"] == alerta.id)
    assert enviada["enviada"] is True
    assert enviada["fecha_enviada"] is not None
    assert enviada["usuario_nombre"] == actor.user.nombre


def test_enviadas_ultimos_dias_acota_el_historial(client, admin_headers, crear_usuario, db_session):
    """El panel del dashboard pide pendientes + historial de 7 días en una sola llamada."""
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=4))
    _generar(client, admin_headers)
    alerta = _pendientes_de(db_session, actor.user.id)[0]
    client.post(f"/alertas/{alerta.id}/marcar-enviada", headers=admin_headers)

    # Dentro de la ventana: aparece.
    dentro = client.get("/alertas/?solo_pendientes=false&enviadas_ultimos_dias=7", headers=admin_headers).json()
    assert alerta.id in [a["id"] for a in dentro]

    # Envejecida más allá de la ventana: desaparece.
    db_session.query(models.AlertaMembresia).filter_by(id=alerta.id).update(
        {"fecha_enviada": datetime.utcnow() - timedelta(days=30)}
    )
    db_session.commit()
    fuera = client.get("/alertas/?solo_pendientes=false&enviadas_ultimos_dias=7", headers=admin_headers).json()
    assert alerta.id not in [a["id"] for a in fuera]


def test_contar_pendientes(client, admin_headers, crear_usuario):
    crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=5))
    _generar(client, admin_headers)
    r = client.get("/alertas/contar", headers=admin_headers)
    assert r.json()["pendientes"] == 2


def test_descartar_alerta(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    _generar(client, admin_headers)
    alerta = _pendientes_de(db_session, actor.user.id)[0]
    assert client.delete(f"/alertas/{alerta.id}", headers=admin_headers).status_code == 204
    assert client.delete(f"/alertas/{alerta.id}", headers=admin_headers).status_code == 404


def test_alertas_cliente_403(client, cliente):
    assert client.get("/alertas/", headers=cliente.headers).status_code == 403
    assert client.get("/alertas/contar", headers=cliente.headers).status_code == 403
    assert client.post("/alertas/generar", headers=cliente.headers).status_code == 403
    assert client.post("/alertas/enviar-whatsapp", headers=cliente.headers).status_code == 403


# ── Envío automático por WhatsApp ────────────────────────────────────
#
# La ventana del PANEL sigue siendo VENTANA_DIAS (7); la del ENVÍO es
# DIAS_ENVIO_AUTOMATICO (3). Los tests de arriba, que no se tocaron, son el
# chequeo de que la primera no se movió.


@pytest.fixture
def wa_activo(monkeypatch):
    """Habilita el envío con un transporte falso. Devuelve los requests
    capturados para poder contar cuántos mensajes salieron de verdad."""

    def _armar(respuesta=None):
        capturados = []

        def _handler(request):
            capturados.append(request)
            if callable(respuesta):
                return respuesta(request)
            return httpx.Response(200, json={"messages": [{"id": "wamid.TEST"}]})

        monkeypatch.setattr(whatsapp, "HABILITADO", True)
        monkeypatch.setattr(whatsapp, "WA_PHONE_NUMBER_ID", "1234567890")
        monkeypatch.setattr(whatsapp, "WA_ACCESS_TOKEN", "token-de-prueba")
        monkeypatch.setattr(whatsapp, "WA_DRY_RUN", False)
        monkeypatch.setattr(
            whatsapp, "_cliente",
            lambda: httpx.Client(transport=httpx.MockTransport(_handler)),
        )
        return capturados

    return _armar


def _enviar(client, headers):
    return client.post("/alertas/enviar-whatsapp", headers=headers)


def _alerta_de(db_session, usuario_id):
    db_session.expire_all()
    return (
        db_session.query(models.AlertaMembresia)
        .filter_by(usuario_id=usuario_id)
        .one()
    )


def test_sin_credenciales_no_envia_nada(client, admin_headers, crear_usuario, db_session):
    """Degradación segura: sin config el sistema sigue en modo manual."""
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=1))
    _generar(client, admin_headers)

    r = _enviar(client, admin_headers)

    assert r.json() == {"enviadas": 0, "fallidas": 0, "omitidas": 0}
    alerta = _alerta_de(db_session, actor.user.id)
    assert alerta.enviada is False
    assert alerta.intentos == 0


def test_envia_dentro_de_la_ventana_de_tres_dias(client, admin_headers, crear_usuario,
                                                 db_session, wa_activo):
    capturados = wa_activo()
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=3))
    _generar(client, admin_headers)

    r = _enviar(client, admin_headers)

    assert r.json()["enviadas"] == 1
    assert len(capturados) == 1
    alerta = _alerta_de(db_session, actor.user.id)
    assert alerta.enviada is True
    assert alerta.canal == "whatsapp_api"
    assert alerta.wa_message_id == "wamid.TEST"
    assert alerta.fecha_enviada is not None
    assert alerta.error_envio is None
    assert alerta.intentos == 1


def test_no_envia_a_quien_todavia_le_faltan_seis_dias(client, admin_headers, crear_usuario,
                                                      db_session, wa_activo):
    """La alerta existe (el panel la muestra desde los 7 días) pero el mensaje
    no sale hasta que falten 3 o menos."""
    capturados = wa_activo()
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=6))
    _generar(client, admin_headers)
    assert len(_pendientes_de(db_session, actor.user.id)) == 1

    r = _enviar(client, admin_headers)

    assert r.json()["enviadas"] == 0
    assert capturados == []
    assert _alerta_de(db_session, actor.user.id).enviada is False


def test_segunda_corrida_no_reenvia(client, admin_headers, crear_usuario, db_session, wa_activo):
    capturados = wa_activo()
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    _generar(client, admin_headers)

    _enviar(client, admin_headers)
    r = _enviar(client, admin_headers)

    assert r.json()["enviadas"] == 0
    assert len(capturados) == 1
    assert _alerta_de(db_session, actor.user.id).intentos == 1


def test_regenerar_despues_de_enviar_no_recrea_la_alerta(client, admin_headers, crear_usuario,
                                                         db_session, wa_activo):
    """La capa fuerte de idempotencia: un socio recibe un solo mensaje por
    ciclo de membresía aunque el job corra todos los días."""
    capturados = wa_activo()
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    _generar(client, admin_headers)
    _enviar(client, admin_headers)

    _generar(client, admin_headers)
    _enviar(client, admin_headers)

    assert len(capturados) == 1
    assert db_session.query(models.AlertaMembresia).filter_by(
        usuario_id=actor.user.id
    ).count() == 1


def test_error_de_meta_deja_la_alerta_pendiente_y_frena_a_los_tres_intentos(
    client, admin_headers, crear_usuario, db_session, wa_activo
):
    capturados = wa_activo(lambda req: httpx.Response(400, json={
        "error": {"code": 131026, "message": "Message undeliverable"}
    }))
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=1))
    _generar(client, admin_headers)

    r = _enviar(client, admin_headers)
    assert r.json()["fallidas"] == 1
    alerta = _alerta_de(db_session, actor.user.id)
    assert alerta.enviada is False
    assert "131026" in alerta.error_envio
    assert alerta.intentos == 1

    _enviar(client, admin_headers)
    _enviar(client, admin_headers)
    assert _alerta_de(db_session, actor.user.id).intentos == 3

    # Cuarta corrida: MAX_INTENTOS ya cortó, no se vuelve a salir a la red.
    _enviar(client, admin_headers)
    assert len(capturados) == 3
    assert _alerta_de(db_session, actor.user.id).intentos == 3


def test_sin_telefono_se_omite_sin_gastar_intentos(client, admin_headers, crear_usuario,
                                                   db_session, wa_activo):
    capturados = wa_activo()
    actor = crear_usuario("cliente", telefono=None,
                          fecha_vencimiento=date.today() + timedelta(days=1))
    _generar(client, admin_headers)

    r = _enviar(client, admin_headers)

    assert r.json()["omitidas"] == 1
    assert capturados == []
    alerta = _alerta_de(db_session, actor.user.id)
    assert alerta.error_envio == "Sin teléfono utilizable"
    assert alerta.intentos == 0
    assert alerta.enviada is False


def test_max_por_corrida_acota_la_tanda(client, admin_headers, crear_usuario, wa_activo, monkeypatch):
    capturados = wa_activo()
    monkeypatch.setattr(whatsapp, "WA_MAX_POR_CORRIDA", 2)
    for _ in range(5):
        crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=1))
    _generar(client, admin_headers)

    r = _enviar(client, admin_headers)

    assert r.json()["enviadas"] == 2
    assert len(capturados) == 2


def test_marcar_enviada_registra_canal_manual(client, admin_headers, crear_usuario, db_session):
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    _generar(client, admin_headers)
    alerta = _pendientes_de(db_session, actor.user.id)[0]

    client.post(f"/alertas/{alerta.id}/marcar-enviada", headers=admin_headers)

    assert _alerta_de(db_session, actor.user.id).canal == "manual"


def test_marcar_enviada_no_pisa_el_canal_automatico(client, admin_headers, crear_usuario,
                                                    db_session, wa_activo):
    wa_activo()
    actor = crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=1))
    _generar(client, admin_headers)
    alerta_id = _pendientes_de(db_session, actor.user.id)[0].id
    _enviar(client, admin_headers)

    client.post(f"/alertas/{alerta_id}/marcar-enviada", headers=admin_headers)

    assert _alerta_de(db_session, actor.user.id).canal == "whatsapp_api"


def test_listado_expone_canal_y_error(client, admin_headers, crear_usuario):
    crear_usuario("cliente", fecha_vencimiento=date.today() + timedelta(days=2))
    _generar(client, admin_headers)

    fila = client.get("/alertas/", headers=admin_headers).json()[0]

    assert "canal" in fila and fila["canal"] is None
    assert "error_envio" in fila and fila["error_envio"] is None


def test_generar_informa_si_el_automatico_esta_activo(client, admin_headers, wa_activo):
    assert _generar(client, admin_headers).json()["whatsapp_automatico"] is False
    wa_activo()
    assert _generar(client, admin_headers).json()["whatsapp_automatico"] is True
