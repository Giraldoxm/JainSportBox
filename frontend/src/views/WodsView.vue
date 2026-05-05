<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-black text-gray-800 tracking-tight">WOD</h2>
        <p class="text-gray-500 mt-1">Workout of the Day</p>
      </div>
      <button
        v-if="puedeEditar"
        @click="abrirFormulario()"
        class="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 px-5 rounded-lg shadow transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo WOD
      </button>
    </div>

    <!-- WODs de hoy -->
    <div class="mb-8">
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">Hoy · {{ fechaHoy }}</h3>

      <div v-if="wodsHoy.length > 0" class="space-y-4">
        <div
          v-for="wod in wodsHoy"
          :key="wod.id"
          class="rounded-2xl p-6 text-white shadow-xl transition-opacity"
          :class="wod.activo ? 'bg-gradient-to-br from-red-500 to-red-700' : 'bg-gradient-to-br from-gray-400 to-gray-600 opacity-70'"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <p class="text-xs font-semibold uppercase tracking-widest" :class="wod.activo ? 'text-red-200' : 'text-gray-300'">
                  WOD del Día
                </p>
                <span
                  v-if="puedeEditar"
                  class="text-xs font-bold px-2 py-0.5 rounded-full"
                  :class="wod.activo ? 'bg-green-500/30 text-green-200' : 'bg-gray-500/40 text-gray-300'"
                >
                  {{ wod.activo ? 'Activo' : 'Inactivo' }}
                </span>
              </div>
              <h3 class="text-2xl font-black mb-3">{{ wod.titulo }}</h3>
              <p class="whitespace-pre-line leading-relaxed" :class="wod.activo ? 'text-red-100' : 'text-gray-300'">
                {{ wod.descripcion }}
              </p>
            </div>
            <div v-if="puedeEditar" class="flex gap-2 ml-4 flex-shrink-0">
              <!-- Toggle activo/inactivo -->
              <button
                @click="toggleWod(wod)"
                :title="wod.activo ? 'Desactivar' : 'Activar'"
                class="p-2 rounded-lg transition-colors"
                :class="wod.activo ? 'bg-white/10 hover:bg-yellow-500/40' : 'bg-white/10 hover:bg-green-500/40'"
              >
                <svg v-if="wod.activo" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
              <button @click="abrirFormulario(wod)" class="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
              <button @click="eliminarWod(wod)" class="p-2 rounded-lg bg-white/10 hover:bg-red-500/60 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="!cargando" class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-10 text-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <p class="text-gray-400 font-medium">No hay WOD programado para hoy</p>
        <button v-if="puedeEditar" @click="abrirFormulario()" class="mt-4 text-red-600 font-semibold hover:underline text-sm">
          + Crear WOD de hoy
        </button>
      </div>
    </div>

    <!-- Historial agrupado por fecha -->
    <div v-if="puedeEditar && fechasAnteriores.length > 0">
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">Historial reciente</h3>
      <div class="space-y-6">
        <div v-for="grupo in fechasAnteriores" :key="grupo.fecha">
          <!-- Separador de fecha -->
          <div class="flex items-center gap-3 mb-2">
            <div class="w-10 h-10 rounded-lg bg-gray-100 flex flex-col items-center justify-center flex-shrink-0">
              <span class="text-xs font-bold text-gray-600 leading-none">{{ diaDelMes(grupo.fecha) }}</span>
              <span class="text-xs text-gray-400 leading-none mt-0.5">{{ mesCorto(grupo.fecha) }}</span>
            </div>
            <span class="text-xs font-semibold text-gray-400 uppercase tracking-wide">{{ grupo.fecha }}</span>
          </div>

          <div class="space-y-2 ml-1">
            <div
              v-for="wod in grupo.wods"
              :key="wod.id"
              class="bg-white rounded-xl border border-gray-200 p-4 flex items-start gap-4 hover:shadow-sm transition-shadow"
              :class="{ 'opacity-50': !wod.activo }"
            >
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-0.5">
                  <p class="font-bold text-gray-800 truncate">{{ wod.titulo }}</p>
                  <span
                    class="text-xs font-semibold px-1.5 py-0.5 rounded-full flex-shrink-0"
                    :class="wod.activo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
                  >
                    {{ wod.activo ? 'Activo' : 'Inactivo' }}
                  </span>
                </div>
                <p class="text-sm text-gray-500 line-clamp-2 mt-0.5">{{ wod.descripcion }}</p>
              </div>
              <div class="flex gap-1 flex-shrink-0">
                <button
                  @click="toggleWod(wod)"
                  :title="wod.activo ? 'Desactivar' : 'Activar'"
                  class="p-1.5 rounded-lg transition-colors"
                  :class="wod.activo ? 'text-gray-400 hover:bg-yellow-50 hover:text-yellow-600' : 'text-gray-400 hover:bg-green-50 hover:text-green-600'"
                >
                  <svg v-if="wod.activo" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
                <button @click="abrirFormulario(wod)" class="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-red-600 transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
                <button @click="eliminarWod(wod)" class="p-1.5 rounded-lg text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal formulario -->
    <div v-if="mostrarModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        <div class="p-6 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-lg font-bold text-gray-800">{{ editando ? 'Editar WOD' : 'Nuevo WOD' }}</h3>
          <button @click="cerrarModal" class="p-2 rounded-lg hover:bg-gray-100 text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <form @submit.prevent="guardarWod" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Título</label>
            <input
              v-model="form.titulo"
              type="text"
              required
              placeholder="Ej: AMRAP 20 min"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all"
            />
          </div>
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Fecha</label>
            <input
              v-model="form.fecha"
              type="date"
              required
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all"
            />
          </div>
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Descripción / Movimientos</label>
            <textarea
              v-model="form.descripcion"
              required
              rows="5"
              placeholder="Ej:&#10;5 Pull-ups&#10;10 Push-ups&#10;15 Air Squats"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all resize-none font-mono text-sm"
            ></textarea>
          </div>
          <!-- Toggle activo en el formulario -->
          <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <span class="text-sm font-semibold text-gray-700">Visible para clientes</span>
            <button
              type="button"
              @click="form.activo = !form.activo"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none"
              :class="form.activo ? 'bg-green-500' : 'bg-gray-300'"
            >
              <span
                class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                :class="form.activo ? 'translate-x-6' : 'translate-x-1'"
              />
            </button>
          </div>
          <div v-if="errorForm" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg border border-red-100">
            {{ errorForm }}
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="cerrarModal" class="flex-1 py-2.5 rounded-lg border border-gray-300 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" :disabled="guardando" class="flex-1 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold transition-colors disabled:bg-red-300 flex items-center justify-center gap-2">
              <span v-if="guardando" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ guardando ? 'Guardando...' : (editando ? 'Actualizar' : 'Crear WOD') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const wods = ref([])
const cargando = ref(true)
const mostrarModal = ref(false)
const editando = ref(null)
const guardando = ref(false)
const errorForm = ref('')

const form = ref({ titulo: '', descripcion: '', fecha: '', activo: true })

const userRol = computed(() => localStorage.getItem('userRol') || 'cliente')
const puedeEditar = computed(() => ['admin', 'coach'].includes(userRol.value))

const fechaHoy = computed(() =>
  new Date().toLocaleDateString('es-CO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
)

const hoyISO = computed(() => new Date().toISOString().slice(0, 10))

const wodsHoy = computed(() => wods.value.filter(w => w.fecha === hoyISO.value))

const fechasAnteriores = computed(() => {
  const anteriores = wods.value.filter(w => w.fecha !== hoyISO.value)
  const mapa = {}
  for (const wod of anteriores) {
    if (!mapa[wod.fecha]) mapa[wod.fecha] = []
    mapa[wod.fecha].push(wod)
  }
  return Object.entries(mapa)
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([fecha, wods]) => ({ fecha, wods }))
})

function diaDelMes(fecha) {
  return new Date(fecha + 'T12:00:00').getDate()
}

function mesCorto(fecha) {
  return new Date(fecha + 'T12:00:00').toLocaleDateString('es-CO', { month: 'short' })
}

async function cargarWods() {
  cargando.value = true
  try {
    const { data } = await api.get('/wods/')
    wods.value = data
  } finally {
    cargando.value = false
  }
}

function abrirFormulario(wod = null) {
  editando.value = wod
  errorForm.value = ''
  if (wod) {
    form.value = { titulo: wod.titulo, descripcion: wod.descripcion, fecha: wod.fecha, activo: wod.activo }
  } else {
    form.value = { titulo: '', descripcion: '', fecha: hoyISO.value, activo: true }
  }
  mostrarModal.value = true
}

function cerrarModal() {
  mostrarModal.value = false
  editando.value = null
}

async function guardarWod() {
  guardando.value = true
  errorForm.value = ''
  try {
    if (editando.value) {
      await api.put(`/wods/${editando.value.id}`, form.value)
    } else {
      await api.post('/wods/', form.value)
    }
    cerrarModal()
    await cargarWods()
  } catch (e) {
    errorForm.value = e.response?.data?.detail || 'Error al guardar el WOD.'
  } finally {
    guardando.value = false
  }
}

async function toggleWod(wod) {
  try {
    const { data } = await api.patch(`/wods/${wod.id}/toggle`)
    const idx = wods.value.findIndex(w => w.id === wod.id)
    if (idx !== -1) wods.value[idx] = data
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al cambiar estado del WOD.')
  }
}

async function eliminarWod(wod) {
  if (!confirm(`¿Eliminar el WOD "${wod.titulo}"?`)) return
  try {
    await api.delete(`/wods/${wod.id}`)
    await cargarWods()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al eliminar.')
  }
}

onMounted(cargarWods)
</script>
