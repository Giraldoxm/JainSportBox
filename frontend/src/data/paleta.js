// Paleta del proyecto — fuente única de los colores categóricos.
//
// El núcleo semántico son 4 familias de Tailwind y NO se usan para datos
// categóricos (ver la sección "Paleta de colores" en CLAUDE.md):
//   gray    → neutro / chrome
//   red     → marca, acción primaria, destructivo
//   emerald → éxito / vigente
//   amber   → alerta / por vencer
//
// Para datos sin semántica (categoría de ejercicio) se usa un badge neutro con un
// punto de color de la escala de abajo. El punto identifica sin competir con el
// rojo/verde/ámbar. Único consumidor hoy: WodEjerciciosEditor, donde la categoría
// va inline junto al nombre y no hay columna que la rotule. En la tabla de
// /ejercicios la categoría va como texto plano: ahí el color no desambigua nada.
//
// OJO: las clases van como strings completos, nunca interpoladas (`bg-${x}-500`),
// porque el scanner de content de tailwind.config.js no resuelve interpolación y
// purgaría la clase del build.

/** Clase base del badge categórico (el color lo aporta el punto). */
export const BADGE_NEUTRO = 'bg-gray-100 text-gray-700'

/** Escala categórica: 5 hues fríos, ninguno confundible con éxito/alerta/peligro. */
export const CATEGORICOS = ['bg-sky-500', 'bg-slate-600', 'bg-violet-500', 'bg-fuchsia-500', 'bg-gray-400']

/** Punto por categoría de ejercicio. */
export const CATEGORIA_EJERCICIO = {
  'Cardio':   'bg-sky-500',
  'Fuerza':   'bg-slate-600',
  'Gimnasia': 'bg-violet-500',
  'Olímpico': 'bg-fuchsia-500',
  'Otro':     'bg-gray-400',
}

/** Categorías de ejercicio en orden de UI (chips de filtro y select del form). */
export const CATEGORIAS_EJERCICIO = ['Cardio', 'Fuerza', 'Gimnasia', 'Olímpico', 'Otro']

export function puntoCategoria(cat) {
  return CATEGORIA_EJERCICIO[cat] || 'bg-gray-400'
}
