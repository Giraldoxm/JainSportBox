"""Reglas de vigencia de la membresía: fecha de vencimiento e ingresos restantes.

Vive aparte porque **cuatro caminos distintos aplican un plan** —`POST /pagos/`,
`POST /pagos/directo/`, `POST /usuarios/{id}/activar` y la anulación que revierte—
y si la regla de los ingresos se escribiera en cada uno, alcanzaría con olvidarse
de uno para que un socio quedara con ingresos que nadie descuenta.

Hay **dos ejes de vigencia** y se validan juntos (ver `_validar_membresia` en
`routers/asistencia.py`):

* `Usuario.fecha_vencimiento` — hasta cuándo vale la membresía. Aplica siempre.
* `Usuario.ingresos_restantes` — cuántas entradas le quedan. `None` significa
  "no aplica" (plan por tiempo); un entero, que la membresía es por ingresos.

Un plan por ingresos (`Plan.numero_ingresos`) caduca por las dos cosas: se acaban
las entradas **o** se pasa la fecha, lo que ocurra primero.
"""

from datetime import date, timedelta
from typing import Optional

from models import Plan, Usuario


def extender_vencimiento(usuario: Usuario, dias: int, hoy: date) -> date:
    """Suma `dias` al vencimiento vigente, o desde hoy si ya venció.

    Renovar antes de tiempo no le quita los días que le quedaban: la base es la
    fecha de vencimiento actual mientras siga vigente.
    """
    base = (
        usuario.fecha_vencimiento
        if (usuario.fecha_vencimiento and usuario.fecha_vencimiento >= hoy)
        else hoy
    )
    usuario.fecha_vencimiento = base + timedelta(days=dias)
    return usuario.fecha_vencimiento


def aplicar_plan(usuario: Usuario, plan: Plan, hoy: date) -> date:
    """Aplica un plan al usuario: extiende la vigencia y ajusta los ingresos."""
    nueva_fecha = extender_vencimiento(usuario, plan.duracion_dias, hoy)

    if plan.por_ingresos:
        # Los ingresos se SUMAN a los que le quedaban, por el mismo criterio con el
        # que la fecha se extiende en vez de pisarse: quien renueva antes de gastar
        # su bono no pierde lo que ya pagó.
        usuario.ingresos_restantes = (usuario.ingresos_restantes or 0) + plan.numero_ingresos
    else:
        # Plan por tiempo: la membresía deja de estar limitada por ingresos. Sin
        # este reset, un socio que antes tuvo un bono agotado (0 ingresos) quedaría
        # bloqueado pese a acabar de pagar la mensualidad.
        usuario.ingresos_restantes = None

    return nueva_fecha


def revertir_plan(usuario: Usuario, dias: int, ingresos: Optional[int]) -> None:
    """Deshace lo que aplicó un pago. Lo usa la anulación.

    La fecha puede quedar en el pasado — es correcto: la membresía venció por la
    reversión. Los ingresos no bajan de 0.

    Limitación conocida: si el pago anulado era de un plano por tiempo, `aplicar_plan`
    puso `ingresos_restantes = None` y los ingresos que hubiera antes no se
    guardaron en ningún lado, así que no se pueden restaurar. Anular ese pago deja
    la membresía como "por tiempo" vencida, que es el desenlace razonable.
    """
    if usuario.fecha_vencimiento and dias:
        usuario.fecha_vencimiento = usuario.fecha_vencimiento - timedelta(days=dias)
    if ingresos and usuario.ingresos_restantes is not None:
        usuario.ingresos_restantes = max(0, usuario.ingresos_restantes - ingresos)


def descontar_ingreso(usuario: Usuario) -> None:
    """Descuenta una entrada si la membresía es por ingresos. No baja de 0."""
    if usuario.ingresos_restantes is not None:
        usuario.ingresos_restantes = max(0, usuario.ingresos_restantes - 1)
