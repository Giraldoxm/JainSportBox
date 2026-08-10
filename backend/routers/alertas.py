from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from fechas import hoy_bogota
from models import AlertaMembresia, RolUsuario, Usuario
from schemas.alerta import AlertaResponse
from security import get_current_user

router = APIRouter(prefix="/alertas", tags=["Alertas"])

# Ventana del PANEL: a partir de acá el vencimiento aparece en el Resumen.
VENTANA_DIAS = 7

# Ventana del ENVÍO automático por WhatsApp, más chica a propósito: el admin ve
# la semana completa, pero al socio se le escribe recién cuando falta poco.
DIAS_ENVIO_AUTOMATICO = 3

# Tope de reintentos por alerta. Un número que Meta rechaza de forma permanente
# (p. ej. 131026, no existe en WhatsApp) si no se reintentaría para siempre.
MAX_INTENTOS = 3

# Se guarda en error_envio para que el panel muestre por qué esa fila no salió.
SIN_TELEFONO = "Sin teléfono utilizable"


def _require_admin_or_coach(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol not in (RolUsuario.ADMIN, RolUsuario.COACH):
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    return current_user


def generar_alertas(db: Session) -> int:
    """Crea una alerta por usuario en cuanto entra en la ventana de 7 días antes del vencimiento.
    No genera duplicados: una sola alerta pendiente por usuario. Si el usuario renovó
    (fecha_vencimiento cambió), se descartan las alertas pendientes obsoletas."""
    hoy = hoy_bogota()
    limite = hoy + timedelta(days=VENTANA_DIAS)
    creadas = 0

    # 1) Limpiar alertas pendientes obsoletas: el usuario renovó o ya salió de la ventana.
    pendientes = db.query(AlertaMembresia).filter(AlertaMembresia.enviada == False).all()
    for a in pendientes:
        u = a.usuario
        if (
            not u
            or not u.fecha_vencimiento
            or u.fecha_vencimiento != a.fecha_vencimiento
            or u.fecha_vencimiento < hoy
            or u.fecha_vencimiento > limite
        ):
            db.delete(a)

    db.flush()

    # 2) Generar alertas faltantes para usuarios dentro de la ventana.
    usuarios = (
        db.query(Usuario)
        .filter(
            Usuario.fecha_vencimiento >= hoy,
            Usuario.fecha_vencimiento <= limite,
        )
        .all()
    )

    for u in usuarios:
        ya_tiene_pendiente = db.query(AlertaMembresia).filter(
            AlertaMembresia.usuario_id == u.id,
            AlertaMembresia.enviada == False,
        ).first()
        if ya_tiene_pendiente:
            continue

        existe_para_fecha = db.query(AlertaMembresia).filter(
            AlertaMembresia.usuario_id == u.id,
            AlertaMembresia.fecha_vencimiento == u.fecha_vencimiento,
        ).first()
        if existe_para_fecha:
            continue

        dias = (u.fecha_vencimiento - hoy).days
        db.add(AlertaMembresia(
            usuario_id=u.id,
            fecha_vencimiento=u.fecha_vencimiento,
            dias_anticipacion=dias,
        ))
        creadas += 1

    db.commit()
    return creadas


def _texto_cuando(dias: int) -> str:
    """Espeja el 'cuando' de whatsappAlerta() en DashboardView.vue.
    Si cambia uno, cambiar el otro: el mensaje manual y el automático deberían
    decir lo mismo."""
    if dias <= 0:
        return "hoy"
    if dias == 1:
        return "mañana"
    return f"en {dias} días"


def enviar_pendientes(db: Session) -> dict:
    """Manda por la Cloud API las alertas pendientes a las que ya les faltan
    DIAS_ENVIO_AUTOMATICO días o menos.

    Idempotente en tres capas:
      1) generar_alertas no recrea una alerta para un (usuario, vencimiento)
         que ya tiene registro, aunque esté enviada → un socio recibe como
         máximo un mensaje por ciclo de membresía, corra este job las veces
         que corra.
      2) acá solo se tocan las que tienen enviada == False.
      3) MAX_INTENTOS frena el reintento infinito de un número inválido.
    """
    import whatsapp

    if not whatsapp.HABILITADO:
        return {"enviadas": 0, "fallidas": 0, "omitidas": 0}

    hoy = hoy_bogota()
    limite = hoy + timedelta(days=DIAS_ENVIO_AUTOMATICO)

    # El filtro va contra Usuario.fecha_vencimiento, NO contra
    # AlertaMembresia.dias_anticipacion: esa columna se congela al crear la
    # alerta y para cuando toca enviar ya está desactualizada.
    pendientes = (
        db.query(AlertaMembresia)
        .join(Usuario, AlertaMembresia.usuario_id == Usuario.id)
        .options(joinedload(AlertaMembresia.usuario))
        .filter(
            AlertaMembresia.enviada == False,
            AlertaMembresia.intentos < MAX_INTENTOS,
            Usuario.fecha_vencimiento != None,
            Usuario.fecha_vencimiento <= limite,
        )
        .order_by(Usuario.fecha_vencimiento.asc())
        .limit(whatsapp.WA_MAX_POR_CORRIDA)
        .all()
    )

    enviadas = fallidas = omitidas = 0

    for a in pendientes:
        u = a.usuario
        telefono = whatsapp.normalizar_telefono(u.telefono if u else None)

        if not telefono:
            # No consume intento: si el admin carga el teléfono, el job la toma
            # al día siguiente sin haber quemado los reintentos.
            if a.error_envio != SIN_TELEFONO:
                a.error_envio = SIN_TELEFONO
                db.commit()
            omitidas += 1
            continue

        dias = (u.fecha_vencimiento - hoy).days
        resultado = whatsapp.enviar_recordatorio(
            telefono,
            u.nombre,
            _texto_cuando(dias),
            u.fecha_vencimiento.strftime("%d/%m/%Y"),
        )

        a.intentos += 1
        if resultado.ok:
            a.enviada = True
            a.fecha_enviada = datetime.utcnow()
            a.canal = "whatsapp_api"
            a.wa_message_id = resultado.message_id
            a.error_envio = None
            enviadas += 1
        else:
            a.error_envio = resultado.error
            fallidas += 1

        # Commit por mensaje, no al final de la tanda: si el proceso muere en
        # el mensaje 18 de 20, así se pierde a lo sumo un registro (→ un posible
        # duplicado); con un commit final se reenviarían los 20.
        db.commit()

    return {"enviadas": enviadas, "fallidas": fallidas, "omitidas": omitidas}


@router.get("/", response_model=List[AlertaResponse])
def listar_alertas(
    solo_pendientes: bool = True,
    enviadas_ultimos_dias: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    """Lista alertas. `enviadas_ultimos_dias` acota el historial a esa ventana.

    Sin esa cota, con `solo_pendientes=false` la consulta devuelve el histórico
    completo, que crece sin techo con los años.
    """
    q = db.query(AlertaMembresia).options(joinedload(AlertaMembresia.usuario))
    if solo_pendientes:
        q = q.filter(AlertaMembresia.enviada == False)
    elif enviadas_ultimos_dias is not None:
        corte = datetime.combine(hoy_bogota() - timedelta(days=enviadas_ultimos_dias), datetime.min.time())
        # Las pendientes (fecha_enviada NULL) siempre entran; el corte aplica al historial.
        q = q.filter(
            (AlertaMembresia.enviada == False) | (AlertaMembresia.fecha_enviada >= corte)
        )
    alertas = q.order_by(AlertaMembresia.dias_anticipacion.asc(), AlertaMembresia.fecha_creacion.desc()).all()
    result = []
    for a in alertas:
        result.append(AlertaResponse(
            id=a.id,
            usuario_id=a.usuario_id,
            usuario_nombre=a.usuario.nombre if a.usuario else "—",
            usuario_telefono=a.usuario.telefono if a.usuario else None,
            fecha_vencimiento=a.fecha_vencimiento,
            dias_anticipacion=a.dias_anticipacion,
            enviada=a.enviada,
            fecha_creacion=a.fecha_creacion,
            fecha_enviada=a.fecha_enviada,
            canal=a.canal,
            error_envio=a.error_envio,
        ))
    return result


@router.post("/generar")
def generar_manualmente(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    import whatsapp

    creadas = generar_alertas(db)
    return {
        "mensaje": f"Proceso completado. {creadas} alerta(s) nueva(s) generada(s).",
        # El panel lo usa para decidir si muestra el botón manual de WhatsApp:
        # con el envío automático andando, ese botón solo estorba salvo que la
        # fila haya fallado.
        "whatsapp_automatico": whatsapp.HABILITADO,
    }


@router.post("/enviar-whatsapp")
def enviar_whatsapp_manual(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    """Dispara la tanda de envío a demanda.

    Es la salida cuando el cron no corrió: `_debo_correr_scheduler()` se evalúa
    una sola vez al importar main, así que en un rolling deploy el proceso nuevo
    puede quedarse sin scheduler si el viejo todavía sostiene el advisory lock.
    No se expone como botón en el Resumen a propósito (ver CLAUDE.md).
    """
    return enviar_pendientes(db)


@router.post("/{alerta_id}/marcar-enviada", status_code=status.HTTP_200_OK)
def marcar_enviada(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    alerta = db.query(AlertaMembresia).filter(AlertaMembresia.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada.")
    alerta.enviada = True
    alerta.fecha_enviada = datetime.utcnow()
    # Sin pisar el canal si ya salió por la API: este endpoint lo dispara el
    # click en el link de wa.me, que es el camino manual.
    if not alerta.canal:
        alerta.canal = "manual"
    db.commit()
    return {"mensaje": "Alerta marcada como enviada."}


@router.delete("/{alerta_id}", status_code=status.HTTP_204_NO_CONTENT)
def descartar_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(_require_admin_or_coach),
):
    alerta = db.query(AlertaMembresia).filter(AlertaMembresia.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada.")
    db.delete(alerta)
    db.commit()
