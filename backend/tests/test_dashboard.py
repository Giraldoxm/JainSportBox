"""Dashboard: KPIs de socios, renovación inferida, inactivos, heatmap y permisos."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import models
from conftest import SessionLocal

TZ_BOGOTA = ZoneInfo("America/Bogota")
UTC = ZoneInfo("UTC")
HOY = date.today()


def _a_utc(dt_local: datetime) -> datetime:
    """Hora de Bogotá → naive UTC, que es como la BD guarda las fechas."""
    return dt_local.replace(tzinfo=TZ_BOGOTA).astimezone(UTC).replace(tzinfo=None)


def _marcar_entrada(usuario_id, cuando_local: datetime):
    db = SessionLocal()
    try:
        db.add(models.Asistencia(
            usuario_id=usuario_id, tipo="entrada", fecha_hora=_a_utc(cuando_local)
        ))
        db.commit()
    finally:
        db.close()


def _pagar(usuario_id, fecha_local: date, dias: int, monto=100_000):
    """Pago personalizado (plan_id NULL) para controlar la duración exacta."""
    db = SessionLocal()
    try:
        db.add(models.Pago(
            usuario_id=usuario_id,
            plan_id=None,
            duracion_dias=dias,
            monto=monto,
            fecha_pago=_a_utc(datetime.combine(fecha_local, time(12, 0))),
        ))
        db.commit()
    finally:
        db.close()


# ── GET /dashboard/resumen ─────────────────────────────────────


def test_resumen_cuenta_socios_por_estado(client, admin_headers, cliente, cliente_vencido, pendiente):
    socios = client.get("/dashboard/resumen", headers=admin_headers).json()["socios"]
    assert socios["activos"] >= 1
    assert socios["vencidos_recuperables"] >= 1   # cliente_vencido venció hace 5 días
    assert socios["pendientes"] >= 1


def test_resumen_no_cuenta_staff_como_socios(client, admin_headers, crear_usuario):
    antes = client.get("/dashboard/resumen", headers=admin_headers).json()["socios"]["activos"]
    crear_usuario("coach", fecha_vencimiento=HOY + timedelta(days=30))
    despues = client.get("/dashboard/resumen", headers=admin_headers).json()["socios"]["activos"]
    assert despues == antes


def test_resumen_por_vencer_incluye_ventana_de_7_dias(client, admin_headers, crear_usuario):
    crear_usuario("cliente", fecha_vencimiento=HOY + timedelta(days=3))
    crear_usuario("cliente", fecha_vencimiento=HOY + timedelta(days=40))
    socios = client.get("/dashboard/resumen", headers=admin_headers).json()["socios"]
    assert socios["por_vencer"] == 1


def test_resumen_asistencia_de_hoy(client, admin_headers, cliente):
    _marcar_entrada(cliente.user.id, datetime.combine(HOY, time(7, 30)))
    asistencia = client.get("/dashboard/resumen", headers=admin_headers).json()["asistencia"]
    assert asistencia["hoy"] == 1
    assert asistencia["engagement"] is not None


def test_resumen_incluye_cumpleaneros(client, admin_headers, crear_usuario):
    """Cubre el criterio de query_cumpleaneros_hoy: cumple hoy Y membresía vigente.

    Las dos exclusiones vivían en el test de `GET /usuarios/cumpleanos-hoy`, que se
    eliminó junto con ese endpoint; el helper sigue vivo acá y sin esto quedaba
    probado solo el caso feliz.
    """
    crear_usuario(
        "cliente",
        fecha_vencimiento=HOY + timedelta(days=30),
        fecha_nacimiento=date(1995, HOY.month, HOY.day),
        nombre="Cumpleañero",
    )
    # Cumple hoy pero con la membresía vencida: no va en la lista.
    crear_usuario(
        "cliente",
        fecha_vencimiento=HOY - timedelta(days=1),
        fecha_nacimiento=date(1990, HOY.month, HOY.day),
        nombre="Vencido",
    )
    # Vigente, pero cumple otro día.
    otro_dia = HOY - timedelta(days=40)
    crear_usuario(
        "cliente",
        fecha_vencimiento=HOY + timedelta(days=30),
        fecha_nacimiento=date(1990, otro_dia.month, otro_dia.day),
        nombre="Otro dia",
    )

    body = client.get("/dashboard/resumen", headers=admin_headers).json()
    assert [c["nombre"] for c in body["cumpleaneros"]] == ["Cumpleañero"]


# ── Tasa de renovación (inferida sobre pagos) ──────────────────


def test_renovacion_cuenta_al_que_volvio_a_pagar(client, admin_headers, crear_usuario):
    # Un pago que venció dentro de la ventana de 30 días + otro pago posterior = renovó.
    socio = crear_usuario("cliente", fecha_vencimiento=HOY + timedelta(days=20))
    vence = HOY - timedelta(days=10)
    _pagar(socio.user.id, vence - timedelta(days=30), dias=30)
    _pagar(socio.user.id, vence, dias=30)

    renovacion = client.get("/dashboard/resumen", headers=admin_headers).json()["renovacion"]
    assert renovacion["vencieron"] >= 1
    assert renovacion["renovaron"] >= 1


def test_renovacion_no_cuenta_al_que_no_volvio(client, admin_headers, crear_usuario):
    socio = crear_usuario("cliente", fecha_vencimiento=HOY - timedelta(days=10))
    vence = HOY - timedelta(days=10)
    _pagar(socio.user.id, vence - timedelta(days=30), dias=30)

    renovacion = client.get("/dashboard/resumen", headers=admin_headers).json()["renovacion"]
    assert renovacion["vencieron"] == 1
    assert renovacion["renovaron"] == 0
    assert renovacion["porcentaje"] == 0


# ── GET /dashboard/inactivos ───────────────────────────────────


def test_inactivos_incluye_socio_que_nunca_vino(client, admin_headers, cliente):
    body = client.get("/dashboard/inactivos", headers=admin_headers).json()
    ids = [s["id"] for s in body["socios"]]
    assert cliente.user.id in ids
    # Nunca marcó: dias_sin_venir queda en None y va primero en la lista.
    assert body["socios"][0]["dias_sin_venir"] is None


def test_inactivos_excluye_al_que_vino_ayer(client, admin_headers, cliente):
    _marcar_entrada(cliente.user.id, datetime.combine(HOY - timedelta(days=1), time(18, 0)))
    body = client.get("/dashboard/inactivos", headers=admin_headers).json()
    assert cliente.user.id not in [s["id"] for s in body["socios"]]


def test_inactivos_incluye_al_que_vino_hace_20_dias(client, admin_headers, cliente):
    _marcar_entrada(cliente.user.id, datetime.combine(HOY - timedelta(days=20), time(18, 0)))
    socios = client.get("/dashboard/inactivos", headers=admin_headers).json()["socios"]
    fila = next(s for s in socios if s["id"] == cliente.user.id)
    assert fila["dias_sin_venir"] == 20


def test_inactivos_excluye_membresia_vencida(client, admin_headers, cliente_vencido):
    body = client.get("/dashboard/inactivos", headers=admin_headers).json()
    assert cliente_vencido.user.id not in [s["id"] for s in body["socios"]]


# ── GET /dashboard/afluencia ───────────────────────────────────


def _lunes_reciente(hace_al_menos=1):
    """Un lunes dentro de la ventana, para no depender del día en que corran los tests."""
    d = HOY - timedelta(days=hace_al_menos)
    while d.weekday() != 0:
        d -= timedelta(days=1)
    return d


def test_afluencia_agrupa_en_hora_de_bogota(client, admin_headers, cliente):
    # 22:00 de Bogotá = 03:00 UTC del día siguiente. Si el agrupado se hiciera en UTC,
    # esta entrada caería en el día equivocado y a las 03:00.
    lunes = _lunes_reciente()
    _marcar_entrada(cliente.user.id, datetime.combine(lunes, time(22, 0)))

    horas = client.get("/dashboard/afluencia", headers=admin_headers).json()["horas"]
    assert [h["hora"] for h in horas] == [22]
    assert horas[0]["semana"] > 0        # cayó en día hábil, a las 22
    assert horas[0]["sabado"] == 0


def test_afluencia_promedia_por_dia_no_suma(client, admin_headers, cliente, crear_usuario):
    """Con 2 entradas la misma hora en 2 lunes distintos, el promedio NO es 2."""
    otro = crear_usuario("cliente", fecha_vencimiento=HOY + timedelta(days=30))
    lunes = _lunes_reciente()
    _marcar_entrada(cliente.user.id, datetime.combine(lunes, time(7, 0)))
    _marcar_entrada(otro.user.id, datetime.combine(lunes - timedelta(days=7), time(7, 0)))

    body = client.get("/dashboard/afluencia", headers=admin_headers).json()
    fila = next(h for h in body["horas"] if h["hora"] == 7)
    # 2 entradas repartidas en todos los días hábiles de la ventana → mucho menos que 2.
    assert 0 < fila["semana"] < 1
    assert body["dias_habiles"] > 2


def test_afluencia_separa_sabado_de_dia_habil(client, admin_headers, cliente):
    sabado = _lunes_reciente() - timedelta(days=2)   # el sábado anterior a ese lunes
    assert sabado.weekday() == 5
    _marcar_entrada(cliente.user.id, datetime.combine(sabado, time(9, 0)))

    fila = next(h for h in client.get("/dashboard/afluencia", headers=admin_headers).json()["horas"] if h["hora"] == 9)
    assert fila["sabado"] > 0
    assert fila["semana"] == 0


def test_afluencia_expone_los_picos(client, admin_headers, cliente):
    lunes = _lunes_reciente()
    _marcar_entrada(cliente.user.id, datetime.combine(lunes, time(7, 0)))
    _marcar_entrada(cliente.user.id, datetime.combine(lunes, time(18, 0)))

    body = client.get("/dashboard/afluencia", headers=admin_headers).json()
    assert body["pico_manana"]["hora"] == 7
    assert body["pico_tarde"]["hora"] == 18


def test_afluencia_vacia_sin_asistencias(client, admin_headers):
    body = client.get("/dashboard/afluencia", headers=admin_headers).json()
    assert body["horas"] == []
    assert body["pico_manana"] is None
    assert body["pico_tarde"] is None


# ── GET /dashboard/socios-mensuales ────────────────────────────


def test_socios_mensuales_sin_pagos_serie_vacia(client, admin_headers, cliente):
    # La serie arranca en el primer pago: sin pagos no hay nada que reconstruir, y
    # dibujar meses en cero mostraría una rampa de crecimiento que nunca ocurrió.
    assert client.get("/dashboard/socios-mensuales", headers=admin_headers).json()["meses"] == []


def test_socios_mensuales_cuenta_la_membresia_vigente_al_cierre(client, admin_headers, cliente):
    _pagar(cliente.user.id, HOY - timedelta(days=40), dias=90)
    meses = client.get("/dashboard/socios-mensuales?meses=6", headers=admin_headers).json()["meses"]
    assert meses[-1]["activos"] == 1        # la ventana de 90 días todavía cubre hoy
    assert meses[-2]["activos"] == 1        # y también el cierre del mes pasado


def test_socios_mensuales_cierra_la_ventana_en_meses_pasados(client, admin_headers, crear_usuario):
    # Pago de hace ~80 días por 30 días: la ventana ya estaba cerrada el mes pasado.
    vencido = crear_usuario("cliente", fecha_vencimiento=HOY - timedelta(days=50))
    _pagar(vencido.user.id, HOY - timedelta(days=80), dias=30)
    meses = client.get("/dashboard/socios-mensuales?meses=6", headers=admin_headers).json()["meses"]
    assert meses[-2]["activos"] == 0


def test_socios_mensuales_ultimo_punto_coincide_con_el_resumen(client, admin_headers, crear_usuario):
    """El invariante que sostiene la credibilidad de la gráfica: el último punto tiene
    que dar el mismo número que la tarjeta Activos.

    El caso difícil es el cliente vigente SIN pago (activado a mano, o sembrado por un
    script de demo): la reconstrucción no lo ve, así que el mes en curso se cuenta
    contra `fecha_vencimiento` en vez de inferirse.
    """
    con_pago = crear_usuario("cliente", fecha_vencimiento=HOY + timedelta(days=20))
    _pagar(con_pago.user.id, HOY - timedelta(days=10), dias=30)
    crear_usuario("cliente", fecha_vencimiento=HOY + timedelta(days=5))   # vigente, sin pago
    crear_usuario("cliente", fecha_vencimiento=HOY - timedelta(days=15))  # vencido

    activos = client.get("/dashboard/resumen", headers=admin_headers).json()["socios"]["activos"]
    meses = client.get("/dashboard/socios-mensuales", headers=admin_headers).json()["meses"]
    assert meses[-1]["activos"] == activos == 2


def test_socios_mensuales_ignora_al_staff(client, admin_headers, crear_usuario):
    coach = crear_usuario("coach", fecha_vencimiento=HOY + timedelta(days=30))
    _pagar(coach.user.id, HOY - timedelta(days=5), dias=30)
    assert client.get("/dashboard/socios-mensuales", headers=admin_headers).json()["meses"] == []


def test_socios_mensuales_cliente_403(client, cliente):
    assert client.get("/dashboard/socios-mensuales", headers=cliente.headers).status_code == 403


# ── GET /dashboard/ingresos-mensuales ──────────────────────────


def test_ingresos_mensuales_serie_continua(client, admin_headers, cliente):
    _pagar(cliente.user.id, HOY, dias=30, monto=150_000)
    meses = client.get("/dashboard/ingresos-mensuales?meses=3", headers=admin_headers).json()["meses"]
    assert len(meses) == 3                      # meses sin movimiento van en cero, no ausentes
    assert meses[-1]["ingresos"] == 150_000
    assert meses[-1]["neto"] == 150_000


# ── Permisos ───────────────────────────────────────────────────


def test_coach_ve_resumen_pero_no_finanzas(client, coach):
    assert client.get("/dashboard/resumen", headers=coach.headers).status_code == 200
    assert client.get("/dashboard/afluencia", headers=coach.headers).status_code == 200
    assert client.get("/dashboard/ingresos-mensuales", headers=coach.headers).status_code == 403


def test_cliente_no_accede_al_dashboard(client, cliente):
    assert client.get("/dashboard/resumen", headers=cliente.headers).status_code == 403
    assert client.get("/dashboard/inactivos", headers=cliente.headers).status_code == 403
