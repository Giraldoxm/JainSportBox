<template>
  <div class="animate-fade-in-up">

    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
      <div>
        <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Mi Salud</h2>
        <p class="text-gray-500 mt-1">Seguimiento de medidas corporales e IMC</p>
      </div>
      <button @click="abrirModal()"
        class="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 px-5 rounded-lg shadow transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        Registrar medidas
      </button>
    </div>

    <!-- Estado vacío -->
    <div v-if="!cargando && medidas.length === 0"
      class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-16 text-center">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
      </svg>
      <p class="text-gray-500 font-semibold text-lg">Aún no tienes registros</p>
      <p class="text-gray-400 text-sm mt-1 mb-5">Empieza registrando tu peso y altura para calcular tu IMC</p>
      <button @click="abrirModal()"
        class="bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 px-6 rounded-lg transition-colors">
        Registrar primera medida
      </button>
    </div>

    <template v-if="medidas.length > 0">

      <!-- Cards últimas medidas -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <!-- IMC -->
        <div class="col-span-2 rounded-2xl p-5 shadow-sm border"
          :class="imcActual.colorFondo">
          <p class="text-xs font-bold uppercase tracking-widest mb-1" :class="imcActual.colorTexto">Índice de Masa Corporal</p>
          <div class="flex items-end gap-3">
            <p class="text-4xl font-black" :class="imcActual.colorTexto">{{ ultima.imc }}</p>
            <span class="text-sm font-bold mb-1 px-2.5 py-0.5 rounded-full" :class="imcActual.badge">
              {{ imcActual.categoria }}
            </span>
          </div>
          <!-- Barra IMC -->
          <div class="mt-3 h-2 bg-white/40 rounded-full overflow-hidden">
            <div class="h-full rounded-full transition-all duration-700"
              :class="imcActual.colorBarra"
              :style="{ width: Math.min(((ultima.imc - 10) / 30) * 100, 100) + '%' }">
            </div>
          </div>
          <div class="flex justify-between text-xs mt-1 font-medium opacity-70" :class="imcActual.colorTexto">
            <span>Bajo</span><span>Normal</span><span>Sobrepeso</span><span>Obesidad</span>
          </div>
        </div>

        <!-- Peso -->
        <div class="bg-white rounded-2xl p-5 border border-blue-100 shadow-sm">
          <p class="text-xs font-bold text-blue-600 uppercase tracking-widest mb-2">Peso actual</p>
          <p class="text-3xl font-black text-gray-900">{{ ultima.peso_kg }}<span class="text-base font-semibold text-gray-400 ml-1">kg</span></p>
          <p v-if="medidas.length > 1" class="text-xs mt-2 font-semibold"
            :class="deltaPeso > 0 ? 'text-red-500' : deltaPeso < 0 ? 'text-emerald-600' : 'text-gray-400'">
            {{ deltaPeso > 0 ? '↑' : deltaPeso < 0 ? '↓' : '=' }}
            {{ deltaPeso !== 0 ? Math.abs(deltaPeso) + ' kg vs anterior' : 'Sin cambio' }}
          </p>
          <p class="text-xs text-gray-400 mt-1">{{ formatFecha(ultima.fecha) }}</p>
        </div>

        <!-- Altura -->
        <div class="bg-white rounded-2xl p-5 border border-violet-100 shadow-sm">
          <p class="text-xs font-bold text-violet-600 uppercase tracking-widest mb-2">Altura</p>
          <p class="text-3xl font-black text-gray-900">{{ ultima.altura_cm }}<span class="text-base font-semibold text-gray-400 ml-1">cm</span></p>
          <p v-if="ultima.cintura_cm" class="text-xs text-gray-500 mt-2">
            Cintura: <span class="font-bold text-gray-700">{{ ultima.cintura_cm }} cm</span>
          </p>
          <p class="text-xs text-gray-400 mt-1">{{ medidas.length }} registro{{ medidas.length !== 1 ? 's' : '' }}</p>
        </div>
      </div>

      <!-- Gráficas -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-6">

        <!-- Gráfica IMC -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-red-500 inline-block"></span>
            Evolución del IMC
          </h3>
          <div class="relative h-52">
            <canvas ref="chartImc"></canvas>
          </div>
        </div>

        <!-- Gráfica Peso -->
        <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
          <h3 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-blue-500 inline-block"></span>
            Evolución del Peso (kg)
          </h3>
          <div class="relative h-52">
            <canvas ref="chartPeso"></canvas>
          </div>
        </div>
      </div>

      <!-- Historial tabla -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="font-bold text-gray-800">Historial de registros</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-100">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-5 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Fecha</th>
                <th class="px-5 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Peso</th>
                <th class="px-5 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Altura</th>
                <th class="px-5 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">IMC</th>
                <th class="px-5 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Cintura</th>
                <th class="px-5 py-3 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">Notas</th>
                <th class="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="m in [...medidas].reverse()" :key="m.id" class="hover:bg-gray-50 transition-colors group">
                <td class="px-5 py-3.5 text-sm font-medium text-gray-700 whitespace-nowrap">{{ formatFecha(m.fecha) }}</td>
                <td class="px-5 py-3.5 text-sm font-bold text-blue-600 whitespace-nowrap">{{ m.peso_kg }} kg</td>
                <td class="px-5 py-3.5 text-sm text-gray-600 whitespace-nowrap">{{ m.altura_cm }} cm</td>
                <td class="px-5 py-3.5 whitespace-nowrap">
                  <span class="text-sm font-bold px-2.5 py-0.5 rounded-full"
                    :class="imcInfo(m.imc).badge">
                    {{ m.imc }} · {{ imcInfo(m.imc).categoria }}
                  </span>
                </td>
                <td class="px-5 py-3.5 text-sm text-gray-500 whitespace-nowrap">{{ m.cintura_cm ? m.cintura_cm + ' cm' : '—' }}</td>
                <td class="px-5 py-3.5 text-sm text-gray-400 max-w-[160px] truncate">{{ m.notas || '—' }}</td>
                <td class="px-5 py-3.5 whitespace-nowrap text-right">
                  <button @click="eliminar(m)"
                    class="opacity-0 group-hover:opacity-100 p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Modal registro -->
    <div v-if="mostrarModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div class="p-6 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-lg font-bold text-gray-800">Registrar medidas</h3>
          <button @click="mostrarModal = false" class="p-2 rounded-lg hover:bg-gray-100 text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <form @submit.prevent="guardar" class="p-6 space-y-4">

          <!-- Preview IMC en tiempo real -->
          <div v-if="form.peso_kg && form.altura_cm"
            class="rounded-xl p-4 text-center transition-all"
            :class="imcInfo(imcPreview).colorFondo">
            <p class="text-xs font-bold uppercase tracking-widest mb-1" :class="imcInfo(imcPreview).colorTexto">IMC calculado</p>
            <p class="text-3xl font-black" :class="imcInfo(imcPreview).colorTexto">{{ imcPreview }}</p>
            <p class="text-sm font-semibold mt-1" :class="imcInfo(imcPreview).colorTexto">{{ imcInfo(imcPreview).categoria }}</p>
          </div>

          <!-- Fecha -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Fecha</label>
            <input v-model="form.fecha" type="date" required
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none">
          </div>

          <!-- Peso y Altura -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Peso (kg) *</label>
              <input v-model.number="form.peso_kg" type="number" step="0.1" min="20" max="500" required
                placeholder="Ej: 75.5"
                class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none">
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Altura (cm) *</label>
              <input v-model.number="form.altura_cm" type="number" step="0.1" min="50" max="300" required
                placeholder="Ej: 175"
                class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none">
            </div>
          </div>

          <!-- Cintura -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">
              Cintura (cm) <span class="text-gray-400 font-normal">(opcional)</span>
            </label>
            <input v-model.number="form.cintura_cm" type="number" step="0.1" min="30" max="300"
              placeholder="Ej: 85"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none">
          </div>

          <!-- Notas -->
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">
              Notas <span class="text-gray-400 font-normal">(opcional)</span>
            </label>
            <textarea v-model="form.notas" rows="2" placeholder="Ej: Después del entrenamiento..."
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none resize-none text-sm"></textarea>
          </div>

          <div v-if="errorForm" class="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg p-3">{{ errorForm }}</div>

          <div class="flex gap-3 pt-2">
            <button type="button" @click="mostrarModal = false"
              class="flex-1 py-2.5 rounded-xl border border-gray-300 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" :disabled="guardando"
              class="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold transition-colors disabled:bg-red-300 flex items-center justify-center gap-2">
              <span v-if="guardando" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ guardando ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Chart } from 'chart.js/auto'
import api from '../api'

// ── Estado ────────────────────────────────────────────────────
const medidas = ref([])
const cargando = ref(true)
const mostrarModal = ref(false)
const guardando = ref(false)
const errorForm = ref('')

const form = ref({
  fecha: new Date().toISOString().slice(0, 10),
  peso_kg: '',
  altura_cm: '',
  cintura_cm: '',
  notas: '',
})

// ── Charts ────────────────────────────────────────────────────
const chartImc = ref(null)
const chartPeso = ref(null)
let instanciaImc = null
let instanciaPeso = null

// ── Computed ──────────────────────────────────────────────────
const ultima = computed(() => medidas.value[medidas.value.length - 1] || null)

const deltaPeso = computed(() => {
  if (medidas.value.length < 2) return 0
  const prev = medidas.value[medidas.value.length - 2].peso_kg
  return Math.round((ultima.value.peso_kg - prev) * 10) / 10
})

const imcPreview = computed(() => {
  if (!form.value.peso_kg || !form.value.altura_cm) return 0
  const h = form.value.altura_cm / 100
  return Math.round(form.value.peso_kg / (h * h) * 10) / 10
})

const imcActual = computed(() => ultima.value ? imcInfo(ultima.value.imc) : {})

// ── Helpers IMC ───────────────────────────────────────────────
function imcInfo(imc) {
  if (imc < 18.5) return {
    categoria: 'Bajo peso',
    colorTexto: 'text-blue-700',
    colorFondo: 'bg-blue-50 border-blue-100',
    badge: 'bg-blue-100 text-blue-700',
    colorBarra: 'bg-blue-400',
  }
  if (imc < 25) return {
    categoria: 'Normal',
    colorTexto: 'text-emerald-700',
    colorFondo: 'bg-emerald-50 border-emerald-100',
    badge: 'bg-emerald-100 text-emerald-700',
    colorBarra: 'bg-emerald-400',
  }
  if (imc < 30) return {
    categoria: 'Sobrepeso',
    colorTexto: 'text-amber-700',
    colorFondo: 'bg-amber-50 border-amber-100',
    badge: 'bg-amber-100 text-amber-700',
    colorBarra: 'bg-amber-400',
  }
  return {
    categoria: 'Obesidad',
    colorTexto: 'text-red-700',
    colorFondo: 'bg-red-50 border-red-100',
    badge: 'bg-red-100 text-red-700',
    colorBarra: 'bg-red-400',
  }
}

const formatFecha = (f) =>
  new Date(f + 'T12:00:00').toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })

// ── Charts ────────────────────────────────────────────────────
function destruirCharts() {
  if (instanciaImc) { instanciaImc.destroy(); instanciaImc = null }
  if (instanciaPeso) { instanciaPeso.destroy(); instanciaPeso = null }
}

function renderCharts() {
  if (medidas.value.length === 0) return
  destruirCharts()

  const labels = medidas.value.map(m => formatFecha(m.fecha))

  const opcionesBase = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 600 },
    plugins: {
      legend: { display: false },
      tooltip: { mode: 'index', intersect: false },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { font: { size: 11 }, maxTicksLimit: 8, maxRotation: 30 },
      },
      y: {
        grid: { color: '#f3f4f6' },
        ticks: { font: { size: 11 } },
      },
    },
  }

  if (chartImc.value) {
    const valoresImc = medidas.value.map(m => m.imc)
    instanciaImc = new Chart(chartImc.value, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'IMC',
          data: valoresImc,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99,102,241,0.1)',
          borderWidth: 2.5,
          pointBackgroundColor: '#6366f1',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          fill: true,
          tension: 0.35,
        }],
      },
      options: {
        ...opcionesBase,
        scales: {
          ...opcionesBase.scales,
          y: {
            ...opcionesBase.scales.y,
            suggestedMin: Math.max(10, Math.min(...valoresImc) - 3),
            suggestedMax: Math.max(...valoresImc) + 3,
          },
        },
      },
    })
  }

  if (chartPeso.value) {
    const valoresPeso = medidas.value.map(m => m.peso_kg)
    instanciaPeso = new Chart(chartPeso.value, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Peso (kg)',
          data: valoresPeso,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59,130,246,0.1)',
          borderWidth: 2.5,
          pointBackgroundColor: '#3b82f6',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          fill: true,
          tension: 0.35,
        }],
      },
      options: {
        ...opcionesBase,
        scales: {
          ...opcionesBase.scales,
          y: {
            ...opcionesBase.scales.y,
            suggestedMin: Math.max(0, Math.min(...valoresPeso) - 5),
            suggestedMax: Math.max(...valoresPeso) + 5,
          },
        },
      },
    })
  }
}

// Observa medidas: cuando cambian y hay datos, espera dos ticks para
// que el v-if revele los canvas antes de instanciar Chart.
watch(medidas, async (val) => {
  if (val.length === 0) { destruirCharts(); return }
  await nextTick()
  await nextTick()
  renderCharts()
})

// ── Fetch ─────────────────────────────────────────────────────
async function cargar() {
  cargando.value = true
  try {
    const { data } = await api.get('/salud/')
    medidas.value = data
  } finally {
    cargando.value = false
  }
}

// ── CRUD ──────────────────────────────────────────────────────
function abrirModal() {
  form.value = {
    fecha: new Date().toISOString().slice(0, 10),
    peso_kg: '',
    altura_cm: ultima.value?.altura_cm || '',
    cintura_cm: '',
    notas: '',
  }
  errorForm.value = ''
  mostrarModal.value = true
}

async function guardar() {
  guardando.value = true
  errorForm.value = ''
  try {
    await api.post('/salud/', {
      fecha: form.value.fecha,
      peso_kg: form.value.peso_kg,
      altura_cm: form.value.altura_cm,
      cintura_cm: form.value.cintura_cm || null,
      notas: form.value.notas || null,
    })
    mostrarModal.value = false
    await cargar()
  } catch (e) {
    const d = e.response?.data?.detail
    errorForm.value = Array.isArray(d) ? d[0].msg : (d || 'Error al guardar.')
  } finally {
    guardando.value = false
  }
}

async function eliminar(m) {
  if (!confirm(`¿Eliminar el registro del ${formatFecha(m.fecha)}?`)) return
  try {
    await api.delete(`/salud/${m.id}`)
    await cargar()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al eliminar.')
  }
}

onMounted(cargar)
onUnmounted(destruirCharts)
</script>

<style>
.animate-fade-in-up {
  animation: fadeInUp 0.4s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
