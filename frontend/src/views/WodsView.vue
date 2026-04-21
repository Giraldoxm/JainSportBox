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

    <!-- WOD de hoy -->
    <div class="mb-8">
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">Hoy · {{ fechaHoy }}</h3>
      <div v-if="wodHoy" class="bg-gradient-to-br from-red-700 to-black rounded-2xl p-6 text-white shadow-xl">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <p class="text-red-200 text-xs font-semibold uppercase tracking-widest mb-1">WOD del Día</p>
            <h3 class="text-2xl font-black mb-3">{{ wodHoy.titulo }}</h3>
            <p class="text-red-100 whitespace-pre-line leading-relaxed">{{ wodHoy.descripcion }}</p>
          </div>
          <div v-if="puedeEditar" class="flex gap-2 ml-4">
            <button @click="abrirFormulario(wodHoy)" class="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
            <button @click="eliminarWod(wodHoy)" class="p-2 rounded-lg bg-white/10 hover:bg-red-500/60 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
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

    <!-- Historial -->
    <div v-if="puedeEditar && wodsAnteriores.length > 0">
      <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">Historial reciente</h3>
      <div class="space-y-3">
        <div
          v-for="wod in wodsAnteriores"
          :key="wod.id"
          class="bg-white rounded-xl border border-gray-200 p-4 flex items-start gap-4 hover:shadow-sm transition-shadow"
        >
          <div class="w-12 h-12 rounded-lg bg-gray-100 flex flex-col items-center justify-center flex-shrink-0">
            <span class="text-xs font-bold text-gray-500">{{ diaDelMes(wod.fecha) }}</span>
            <span class="text-xs text-gray-400">{{ mesCorto(wod.fecha) }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="font-bold text-gray-800 truncate">{{ wod.titulo }}</p>
            <p class="text-sm text-gray-500 line-clamp-2 mt-0.5">{{ wod.descripcion }}</p>
          </div>
          <div class="flex gap-1 flex-shrink-0">
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

const form = ref({ titulo: '', descripcion: '', fecha: '' })

const userRol = computed(() => localStorage.getItem('userRol') || 'cliente')
const puedeEditar = computed(() => ['admin', 'coach'].includes(userRol.value))

const fechaHoy = computed(() => {
  return new Date().toLocaleDateString('es-CO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
})

const hoyISO = computed(() => new Date().toISOString().slice(0, 10))

const wodHoy = computed(() => wods.value.find(w => w.fecha === hoyISO.value) || null)
const wodsAnteriores = computed(() => wods.value.filter(w => w.fecha !== hoyISO.value))

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
    form.value = { titulo: wod.titulo, descripcion: wod.descripcion, fecha: wod.fecha }
  } else {
    form.value = { titulo: '', descripcion: '', fecha: hoyISO.value }
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
