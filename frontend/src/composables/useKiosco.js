// Modo kiosco de /acceso: la pestaña queda abierta en la PC de recepción con la
// sesión de un coach/admin, y los clientes solo escriben su cédula.
//
// El flag va en **sessionStorage y no en localStorage**, y esto es la decisión
// central del módulo: localStorage se comparte entre todas las pestañas del mismo
// navegador, así que un kiosco activo también bloqueaba la pestaña donde el staff
// estaba trabajando. sessionStorage está aislado por pestaña → recepción queda
// bloqueada y el coach sigue usando el panel en otra pestaña con la misma sesión.
//
// Tampoco sirve un ref en memoria: sessionStorage sobrevive al F5, así que si un
// cliente recarga la pantalla el kiosco sigue puesto. Lo que NO sobrevive es cerrar
// la pestaña — al reabrirla el candado ya no está. Es el precio del aislamiento por
// pestaña y es aceptable: cerrar la pestaña y navegar a otra URL es una acción
// deliberada, no algo que pase por curiosear.
//
// OJO — alcance real del candado: impide el uso casual (navegar por URL, botón
// atrás, F5), no a alguien que abra las devtools y saque el JWT del localStorage.
// Para eso haría falta un token de kiosco con permiso solo de marcar asistencia.

import { ref } from 'vue'

const KEY = 'kioscoAcceso'

export const kioscoActivo = ref(sessionStorage.getItem(KEY) === '1')

// Lee el storage directo (no el ref) para que el guard del router funcione antes de
// que se monte cualquier componente.
export function kioscoBloqueado() {
  return sessionStorage.getItem(KEY) === '1'
}

export function activarKiosco() {
  sessionStorage.setItem(KEY, '1')
  kioscoActivo.value = true
}

export function desactivarKiosco() {
  sessionStorage.removeItem(KEY)
  kioscoActivo.value = false
}
