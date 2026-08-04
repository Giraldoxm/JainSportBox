<script setup>
// Datos de afiliación de un cliente pendiente: lo que el admin necesita confirmar
// antes de activarlo, pero que no justifica una columna propia en el listado.
// Se usa en la fila expandida de la tabla y dentro de la card móvil.
defineProps({ p: { type: Object, required: true } })

const formatFecha = (f) => {
  if (!f) return '—'
  return new Date(f).toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>

<template>
  <div class="space-y-3">
    <dl class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-x-6 gap-y-3 text-xs">
      <div class="min-w-0">
        <dt class="text-gray-400 font-semibold uppercase tracking-wide mb-0.5">Género</dt>
        <dd class="font-semibold text-gray-700 capitalize truncate">{{ p.genero || '—' }}</dd>
      </div>
      <div class="min-w-0">
        <dt class="text-gray-400 font-semibold uppercase tracking-wide mb-0.5">Nacimiento</dt>
        <dd class="font-semibold text-gray-700 truncate">{{ formatFecha(p.fecha_nacimiento) }}</dd>
      </div>
      <div class="min-w-0">
        <dt class="text-gray-400 font-semibold uppercase tracking-wide mb-0.5">EPS</dt>
        <dd class="font-semibold text-gray-700 truncate">{{ p.eps || '—' }}</dd>
      </div>
      <div class="min-w-0">
        <dt class="text-gray-400 font-semibold uppercase tracking-wide mb-0.5">Barrio</dt>
        <dd class="font-semibold text-gray-700 truncate">{{ p.barrio || '—' }}</dd>
      </div>
      <div class="min-w-0 col-span-2 sm:col-span-1">
        <dt class="text-gray-400 font-semibold uppercase tracking-wide mb-0.5">Emergencia</dt>
        <dd class="font-semibold text-gray-700 truncate">{{ p.contacto_emergencia_nombre || '—' }}</dd>
        <dd v-if="p.contacto_emergencia_telefono" class="text-gray-500 truncate">{{ p.contacto_emergencia_telefono }}</dd>
      </div>
    </dl>

    <!-- Menor de edad: ámbar (aviso), no rojo. Ver la paleta en CLAUDE.md. -->
    <div v-if="p.es_menor" class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5">
      <p class="text-[11px] font-bold uppercase tracking-wide text-amber-800 mb-1.5">Datos del acudiente</p>
      <dl class="grid grid-cols-1 sm:grid-cols-3 gap-x-6 gap-y-1 text-xs">
        <div class="min-w-0">
          <dt class="inline text-amber-700/70 font-semibold">Nombre: </dt>
          <dd class="inline font-semibold text-amber-900">{{ p.acudiente_nombre || '—' }}</dd>
        </div>
        <div class="min-w-0">
          <dt class="inline text-amber-700/70 font-semibold">Cédula: </dt>
          <dd class="inline font-semibold text-amber-900">{{ p.acudiente_documento || '—' }}</dd>
        </div>
        <div class="min-w-0">
          <dt class="inline text-amber-700/70 font-semibold">Teléfono: </dt>
          <dd class="inline font-semibold text-amber-900">{{ p.acudiente_telefono || '—' }}</dd>
        </div>
      </dl>
    </div>
  </div>
</template>
