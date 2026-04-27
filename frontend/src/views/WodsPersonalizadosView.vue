<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h2 class="text-3xl font-black text-gray-800 tracking-tight">WODs Personalizados</h2>
        <p class="text-gray-500 mt-1">Entrenamientos especiales por género</p>
      </div>
      <button
        v-if="isAdmin"
        @click="abrirModal()"
        class="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 px-5 rounded-lg shadow transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo WOD
      </button>
    </div>

    <!-- ── VISTA ADMIN ── -->
    <template v-if="isAdmin">
      <!-- Stats hoy -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <div class="bg-blue-50 rounded-2xl p-5 border border-blue-100">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center flex-shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div>
              <p class="text-xs font-bold text-blue-500 uppercase tracking-widest">Masculino hoy</p>
              <p class="text-3xl font-black text-blue-700">{{ countHoy('masculino') }}</p>
              <p class="text-xs text-blue-400">{{ countHoy('masculino') === 1 ? 'WOD programado' : 'WODs programados' }}</p>
            </div>
          </div>
        </div>
        <div class="bg-purple-50 rounded-2xl p-5 border border-purple-100">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div>
              <p class="text-xs font-bold text-purple-500 uppercase tracking-widest">Femenino hoy</p>
              <p class="text-3xl font-black text-purple-700">{{ countHoy('femenino') }}</p>
              <p class="text-xs text-purple-400">{{ countHoy('femenino') === 1 ? 'WOD programado' : 'WODs programados' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Lista de WODs agrupada por fecha -->
      <div v-if="wods.length > 0">
        <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">Todos los WODs</h3>

        <!-- WODs de hoy destacados -->
        <div v-if="wodsHoy.length > 0" class="mb-6 space-y-3">
          <p class="text-xs font-bold text-gray-400 uppercase tracking-wide">Hoy · {{ fechaHoyTexto }}</p>
          <div
            v-for="wod in wodsHoy"
            :key="wod.id"
            class="rounded-2xl p-5 text-white shadow-lg"
            :class="wod.genero_destino === 'masculino'
              ? 'bg-gradient-to-br from-blue-700 to-blue-900'
              : 'bg-gradient-to-br from-purple-700 to-purple-900'"
          >
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <span
                  class="inline-block text-xs font-bold px-2.5 py-1 rounded-full mb-2"
                  :class="wod.genero_destino === 'masculino' ? 'bg-blue-500/40 text-blue-100' : 'bg-purple-500/40 text-purple-100'"
                >
                  {{ wod.genero_destino === 'masculino' ? 'Masculino' : 'Femenino' }}
                </span>
                <h4 class="text-xl font-black mb-1">{{ wod.titulo }}</h4>
                <p class="text-sm whitespace-pre-line leading-relaxed opacity-90">{{ wod.descripcion }}</p>
              </div>
              <button
                @click="eliminarWod(wod)"
                class="p-2 rounded-lg bg-white/10 hover:bg-red-500/50 transition-colors flex-shrink-0"
                title="Eliminar"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Historial -->
        <div v-if="wodsAnteriores.length > 0">
          <p class="text-xs font-bold text-gray-400 uppercase tracking-wide mb-3">Historial</p>
          <div class="space-y-2">
            <div
              v-for="wod in wodsAnteriores"
              :key="wod.id"
              class="bg-white rounded-xl border border-gray-200 p-4 flex items-start gap-4 hover:shadow-sm transition-shadow"
            >
              <div class="w-12 h-12 rounded-xl bg-gray-100 flex flex-col items-center justify-center flex-shrink-0">
                <span class="text-sm font-black text-gray-700 leading-none">{{ diaDelMes(wod.fecha) }}</span>
                <span class="text-xs text-gray-400 leading-none mt-0.5">{{ mesCorto(wod.fecha) }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-0.5">
                  <p class="font-bold text-gray-800 truncate">{{ wod.titulo }}</p>
                  <span
                    class="text-xs font-bold px-2 py-0.5 rounded-full flex-shrink-0"
                    :class="wod.genero_destino === 'masculino' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'"
                  >
                    {{ wod.genero_destino === 'masculino' ? 'Masculino' : 'Femenino' }}
                  </span>
                </div>
                <p class="text-sm text-gray-500 line-clamp-2">{{ wod.descripcion }}</p>
              </div>
              <button
                @click="eliminarWod(wod)"
                class="p-1.5 rounded-lg text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors flex-shrink-0"
                title="Eliminar"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="!cargando" class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-12 text-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-14 w-14 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
        <p class="text-gray-500 font-bold text-lg mb-1">Sin WODs personalizados</p>
        <p class="text-gray-400 text-sm mb-4">Crea el primer WOD personalizado para tus atletas.</p>
        <button @click="abrirModal()" class="text-red-600 font-semibold hover:underline text-sm">
          + Crear el primero
        </button>
      </div>
    </template>

    <!-- ── VISTA CLIENTE ── -->
    <template v-else>
      <!-- Sin acceso al plan -->
      <div v-if="sinAcceso" class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-14 text-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
        <p class="text-lg font-bold text-gray-600 mb-2">Plan no incluido</p>
        <p class="text-gray-400 text-sm max-w-xs mx-auto">Tu plan actual no incluye entrenamientos personalizados. Actualiza tu membresía para acceder.</p>
        <router-link to="/planes" class="inline-block mt-5 bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-5 rounded-lg text-sm transition-colors">
          Ver planes disponibles
        </router-link>
      </div>

      <template v-else>
        <!-- WOD de hoy -->
        <div class="mb-8">
          <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">
            Tu WOD de Hoy · {{ fechaHoyTexto }}
          </h3>

          <div
            v-if="wodDeHoy"
            class="rounded-2xl p-6 text-white shadow-xl"
            :class="colorGradient"
          >
            <div class="flex items-center gap-2 mb-2">
              <p class="text-xs font-semibold uppercase tracking-widest opacity-80">WOD Personalizado</p>
              <span class="text-xs font-bold px-2.5 py-0.5 rounded-full" :class="colorBadge">
                {{ generoLabel }}
              </span>
            </div>
            <h3 class="text-2xl font-black mb-3">{{ wodDeHoy.titulo }}</h3>
            <p class="whitespace-pre-line leading-relaxed opacity-90">{{ wodDeHoy.descripcion }}</p>
          </div>

          <div v-else-if="!cargando" class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-10 text-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-gray-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <p class="text-gray-400 font-medium">No hay WOD personalizado para hoy</p>
            <p class="text-gray-300 text-sm mt-1">Vuelve mañana o consulta el historial.</p>
          </div>
        </div>

        <!-- Historial -->
        <div v-if="wodsAnteriores.length > 0">
          <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">Historial</h3>
          <div class="space-y-2">
            <div
              v-for="wod in wodsAnteriores"
              :key="wod.id"
              class="bg-white rounded-xl border border-gray-200 p-4 flex items-start gap-3 hover:shadow-sm transition-shadow"
            >
              <div
                class="w-11 h-11 rounded-xl flex flex-col items-center justify-center flex-shrink-0"
                :class="generoCliente === 'masculino' ? 'bg-blue-50' : 'bg-purple-50'"
              >
                <span class="text-sm font-black leading-none" :class="generoCliente === 'masculino' ? 'text-blue-700' : 'text-purple-700'">
                  {{ diaDelMes(wod.fecha) }}
                </span>
                <span class="text-xs leading-none mt-0.5" :class="generoCliente === 'masculino' ? 'text-blue-400' : 'text-purple-400'">
                  {{ mesCorto(wod.fecha) }}
                </span>
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-bold text-gray-800 truncate">{{ wod.titulo }}</p>
                <p class="text-sm text-gray-500 line-clamp-2 mt-0.5">{{ wod.descripcion }}</p>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>

    <!-- ── MODAL (solo admin) ── -->
    <div v-if="mostrarModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        <div class="p-6 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-lg font-bold text-gray-800">Nuevo WOD Personalizado</h3>
          <button @click="cerrarModal" class="p-2 rounded-lg hover:bg-gray-100 text-gray-400 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <form @submit.prevent="guardar" class="p-6 space-y-4">
          <!-- Selector de género primero -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">Categoría <span class="text-red-500">*</span></label>
            <div class="grid grid-cols-2 gap-3">
              <button
                type="button"
                @click="form.genero_destino = 'masculino'"
                class="py-3 px-4 rounded-xl border-2 font-bold text-sm transition-all flex items-center justify-center gap-2"
                :class="form.genero_destino === 'masculino'
                  ? 'border-blue-600 bg-blue-600 text-white shadow-md'
                  : 'border-gray-200 text-gray-500 hover:border-blue-300 hover:text-blue-600'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Masculino
              </button>
              <button
                type="button"
                @click="form.genero_destino = 'femenino'"
                class="py-3 px-4 rounded-xl border-2 font-bold text-sm transition-all flex items-center justify-center gap-2"
                :class="form.genero_destino === 'femenino'
                  ? 'border-purple-600 bg-purple-600 text-white shadow-md'
                  : 'border-gray-200 text-gray-500 hover:border-purple-300 hover:text-purple-600'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Femenino
              </button>
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Título</label>
            <input
              v-model="form.titulo"
              type="text"
              required
              placeholder="Ej: AMRAP 20 min — Fuerza"
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
            <button
              type="button"
              @click="cerrarModal"
              class="flex-1 py-2.5 rounded-lg border border-gray-300 text-gray-600 font-semibold hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              :disabled="guardando || !form.genero_destino"
              class="flex-1 py-2.5 rounded-lg text-white font-bold transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              :class="form.genero_destino === 'masculino'
                ? 'bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300'
                : form.genero_destino === 'femenino'
                  ? 'bg-purple-600 hover:bg-purple-700 disabled:bg-purple-300'
                  : 'bg-red-600 hover:bg-red-700 disabled:bg-red-300'"
            >
              <span v-if="guardando" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ guardando ? 'Guardando...' : 'Crear WOD' }}
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
import { useAuth } from '../composables/useAuth'

const { isAdmin } = useAuth()

const wods = ref([])
const cargando = ref(true)
const sinAcceso = ref(false)
const mostrarModal = ref(false)
const guardando = ref(false)
const errorForm = ref('')

const form = ref({ titulo: '', descripcion: '', fecha: '', genero_destino: '' })

const generoCliente = computed(() => localStorage.getItem('userGenero') || '')

const hoyISO = computed(() => new Date().toISOString().slice(0, 10))
const fechaHoyTexto = computed(() =>
  new Date().toLocaleDateString('es-CO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
)

const wodsHoy = computed(() => wods.value.filter(w => w.fecha === hoyISO.value))
const wodDeHoy = computed(() => wods.value.find(w => w.fecha === hoyISO.value) || null)
const wodsAnteriores = computed(() => wods.value.filter(w => w.fecha !== hoyISO.value))

const generoLabel = computed(() =>
  generoCliente.value === 'masculino' ? 'Masculino' : generoCliente.value === 'femenino' ? 'Femenino' : ''
)
const colorGradient = computed(() =>
  generoCliente.value === 'masculino'
    ? 'bg-gradient-to-br from-blue-700 to-blue-900'
    : 'bg-gradient-to-br from-purple-700 to-purple-900'
)
const colorBadge = computed(() =>
  generoCliente.value === 'masculino'
    ? 'bg-blue-500/40 text-blue-100'
    : 'bg-purple-500/40 text-purple-100'
)

function countHoy(genero) {
  return wods.value.filter(w => w.fecha === hoyISO.value && w.genero_destino === genero).length
}

function diaDelMes(fecha) {
  return new Date(fecha + 'T12:00:00').getDate()
}

function mesCorto(fecha) {
  return new Date(fecha + 'T12:00:00').toLocaleDateString('es-CO', { month: 'short' })
}

async function cargar() {
  cargando.value = true
  sinAcceso.value = false
  try {
    const { data } = await api.get('/wods/personalizados')
    wods.value = data
  } catch (e) {
    if (e.response?.status === 403) {
      sinAcceso.value = true
    }
  } finally {
    cargando.value = false
  }
}

function abrirModal() {
  form.value = { titulo: '', descripcion: '', fecha: hoyISO.value, genero_destino: '' }
  errorForm.value = ''
  mostrarModal.value = true
}

function cerrarModal() {
  mostrarModal.value = false
}

async function guardar() {
  if (!form.value.genero_destino) {
    errorForm.value = 'Selecciona la categoría (Masculino o Femenino).'
    return
  }
  guardando.value = true
  errorForm.value = ''
  try {
    await api.post('/wods/', { ...form.value, es_personalizado: true, activo: true })
    cerrarModal()
    await cargar()
  } catch (e) {
    errorForm.value = e.response?.data?.detail || 'Error al crear el WOD.'
  } finally {
    guardando.value = false
  }
}

async function eliminarWod(wod) {
  if (!confirm(`¿Eliminar el WOD "${wod.titulo}"?`)) return
  try {
    await api.delete(`/wods/${wod.id}`)
    await cargar()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al eliminar.')
  }
}

onMounted(cargar)
</script>
