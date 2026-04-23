<template>
  <div class="animate-fade-in-up">

    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
      <div>
        <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Planes de Suscripción</h2>
        <p class="text-gray-500 mt-1">Elige el plan que mejor se adapte a tu entrenamiento</p>
      </div>
      <button v-if="isAdmin" @click="abrirCrear"
        class="bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all font-semibold flex items-center gap-2 transform active:scale-95">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
        </svg>
        Nuevo Plan
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-red-600"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="planes.length === 0" class="text-center py-20 text-gray-400">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <p class="font-semibold text-lg">No hay planes disponibles</p>
      <p v-if="isAdmin" class="text-sm mt-1">Crea el primer plan con el botón de arriba.</p>
    </div>

    <!-- Cards -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="plan in planes" :key="plan.id"
        class="bg-white rounded-2xl shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden flex flex-col">

        <!-- Card header -->
        <div class="bg-gradient-to-br from-gray-900 to-gray-800 px-6 py-6 relative">
          <!-- Admin actions -->
          <div v-if="isAdmin" class="absolute top-3 right-3 flex gap-1">
            <button @click="abrirEditar(plan)" title="Editar"
              class="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button @click="confirmarEliminar(plan)" title="Eliminar"
              class="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>

          <!-- Icon -->
          <div class="w-11 h-11 bg-red-600 rounded-xl flex items-center justify-center mb-4 shadow-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>

          <!-- Name -->
          <h3 class="text-xl font-extrabold text-white leading-tight">{{ plan.nombre }}</h3>

          <!-- Duration badge -->
          <span class="inline-flex items-center gap-1 mt-2 px-3 py-0.5 rounded-full text-xs font-bold bg-white/10 text-gray-300 border border-white/10">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ plan.duracion_dias }} días de acceso
          </span>
        </div>

        <!-- Card body -->
        <div class="px-6 py-5 flex flex-col flex-1 gap-4">

          <!-- Price -->
          <div class="flex items-end gap-1">
            <span class="text-3xl font-black text-gray-900">${{ formatPrecio(plan.precio) }}</span>
            <span class="text-sm text-gray-400 mb-1">COP / período</span>
          </div>

          <!-- Divider -->
          <div class="border-t border-gray-100"></div>

          <!-- Benefits -->
          <ul v-if="plan.beneficios.length" class="space-y-2 flex-1">
            <li v-for="b in plan.beneficios" :key="b" class="flex items-start gap-2.5">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              <span class="text-sm text-gray-600 leading-snug">{{ b }}</span>
            </li>
          </ul>
          <p v-else class="text-sm text-gray-400 italic flex-1">Sin beneficios definidos.</p>

          <!-- Button -->
          <button @click="abrirAdquirir(plan)"
            class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-xl transition-all shadow-sm hover:shadow-md active:scale-95 mt-2">
            Adquirir Plan
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal: Adquirir Plan ── -->
    <div v-if="planAdquiriendo" class="fixed inset-0 flex items-end sm:items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
        <div class="bg-gradient-to-br from-gray-900 to-gray-800 px-6 py-6">
          <div class="w-10 h-10 bg-red-600 rounded-xl flex items-center justify-center mb-3 shadow">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 class="text-xl font-extrabold text-white">{{ planAdquiriendo.nombre }}</h3>
          <div class="flex items-center gap-3 mt-2">
            <span class="text-2xl font-black text-white">${{ formatPrecio(planAdquiriendo.precio) }}</span>
            <span class="text-sm text-gray-400">· {{ planAdquiriendo.duracion_dias }} días</span>
          </div>
        </div>
        <div class="px-6 py-5">
          <ul v-if="planAdquiriendo.beneficios.length" class="space-y-2 mb-5">
            <li v-for="b in planAdquiriendo.beneficios" :key="b" class="flex items-start gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              <span class="text-sm text-gray-600">{{ b }}</span>
            </li>
          </ul>
          <div class="bg-red-50 border border-red-100 rounded-xl p-4 mb-5">
            <p class="text-sm text-red-700 font-semibold">¿Cómo adquirir este plan?</p>
            <p class="text-sm text-red-600 mt-1">
              {{ isAdmin || isCoach
                ? 'Dirígete a la sección Usuarios y asigna este plan desde la opción Renovar membresía.'
                : 'Acércate al box o contacta a tu entrenador para activar este plan.' }}
            </p>
          </div>
          <button @click="planAdquiriendo = null"
            class="w-full py-2.5 rounded-xl bg-gray-900 hover:bg-gray-800 text-white font-semibold transition-colors">
            Cerrar
          </button>
        </div>
      </div>
    </div>

    <!-- ── Modal: Crear / Editar Plan (admin) ── -->
    <div v-if="showForm" class="fixed inset-0 flex items-end sm:items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center px-6 pt-6 pb-0 mb-5">
          <h3 class="text-2xl font-bold text-gray-900">{{ editando ? 'Editar Plan' : 'Nuevo Plan' }}</h3>
          <button @click="cerrarForm" class="text-gray-400 hover:text-gray-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form @submit.prevent="guardarPlan" class="px-6 pb-6 space-y-5">
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nombre del plan <span class="text-red-500">*</span></label>
            <input v-model="form.nombre" type="text" required minlength="2" maxlength="80"
              class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all"
              placeholder="Ej. Plan Mensual">
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Precio (COP) <span class="text-red-500">*</span></label>
              <input v-model.number="form.precio" type="number" required min="1" step="1"
                class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all"
                placeholder="Ej. 100000">
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-1.5">Duración (días) <span class="text-red-500">*</span></label>
              <input v-model.number="form.duracion_dias" type="number" required min="1"
                class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all"
                placeholder="Ej. 30">
            </div>
          </div>

          <div>
            <div class="flex justify-between items-center mb-1.5">
              <label class="block text-sm font-semibold text-gray-700">Beneficios</label>
              <button type="button" @click="agregarBeneficio"
                class="text-xs text-red-600 hover:text-red-700 font-semibold flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
                </svg>
                Agregar
              </button>
            </div>
            <div class="space-y-2">
              <div v-for="(b, i) in form.beneficios" :key="i" class="flex gap-2">
                <input v-model="form.beneficios[i]" type="text"
                  class="flex-1 px-3 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-sm transition-all"
                  :placeholder="`Beneficio ${i + 1}`">
                <button type="button" @click="eliminarBeneficio(i)"
                  class="p-2.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <button v-if="form.beneficios.length === 0" type="button" @click="agregarBeneficio"
                class="w-full py-3 border-2 border-dashed border-gray-200 rounded-lg text-sm text-gray-400 hover:border-red-300 hover:text-red-400 transition-colors">
                + Agregar primer beneficio
              </button>
            </div>
          </div>

          <div v-if="errorForm" class="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg p-3">{{ errorForm }}</div>

          <div class="flex gap-3 pt-2 border-t border-gray-100">
            <button type="button" @click="cerrarForm"
              class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" :disabled="guardando"
              class="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold transition-colors disabled:bg-red-300 flex items-center justify-center gap-2">
              <span v-if="guardando" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ guardando ? 'Guardando...' : (editando ? 'Guardar cambios' : 'Crear Plan') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ── Modal: Confirmar eliminación ── -->
    <div v-if="planAEliminar" class="fixed inset-0 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-sm shadow-2xl p-6">
        <div class="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 class="text-lg font-bold text-gray-900 text-center">Eliminar Plan</h3>
        <p class="text-sm text-gray-500 text-center mt-2">
          ¿Estás seguro de eliminar <span class="font-semibold text-gray-700">{{ planAEliminar.nombre }}</span>? Esta acción no se puede deshacer.
        </p>
        <div class="flex gap-3 mt-6">
          <button @click="planAEliminar = null"
            class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">
            Cancelar
          </button>
          <button @click="ejecutarEliminar" :disabled="eliminando"
            class="flex-1 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold transition-colors disabled:bg-red-300 flex items-center justify-center gap-2">
            <span v-if="eliminando" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
            {{ eliminando ? 'Eliminando...' : 'Eliminar' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { useAuth } from '../composables/useAuth'

const { isAdmin, isCoach } = useAuth()

const planes = ref([])
const loading = ref(true)

const planAdquiriendo = ref(null)
const planAEliminar = ref(null)
const eliminando = ref(false)

const showForm = ref(false)
const editando = ref(null)
const guardando = ref(false)
const errorForm = ref('')
const form = ref({ nombre: '', precio: '', duracion_dias: '', beneficios: [] })

const formatPrecio = (v) => Number(v).toLocaleString('es-CO')

const fetchPlanes = async () => {
  loading.value = true
  try { planes.value = (await api.get('/planes/')).data }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

const abrirAdquirir = (plan) => { planAdquiriendo.value = plan }

const abrirCrear = () => {
  editando.value = null
  form.value = { nombre: '', precio: '', duracion_dias: '', beneficios: [] }
  errorForm.value = ''
  showForm.value = true
}

const abrirEditar = (plan) => {
  editando.value = plan
  form.value = {
    nombre: plan.nombre,
    precio: plan.precio,
    duracion_dias: plan.duracion_dias,
    beneficios: [...plan.beneficios],
  }
  errorForm.value = ''
  showForm.value = true
}

const cerrarForm = () => { showForm.value = false; editando.value = null }

const agregarBeneficio = () => { form.value.beneficios.push('') }
const eliminarBeneficio = (i) => { form.value.beneficios.splice(i, 1) }

const guardarPlan = async () => {
  guardando.value = true
  errorForm.value = ''
  const payload = {
    nombre: form.value.nombre,
    precio: form.value.precio,
    duracion_dias: form.value.duracion_dias,
    beneficios: form.value.beneficios.filter(b => b.trim()),
  }
  try {
    if (editando.value) {
      await api.patch(`/planes/${editando.value.id}`, payload)
    } else {
      await api.post('/planes/', payload)
    }
    cerrarForm()
    await fetchPlanes()
  } catch (e) {
    errorForm.value = e.response?.data?.detail || 'Error al guardar el plan.'
  } finally {
    guardando.value = false
  }
}

const confirmarEliminar = (plan) => { planAEliminar.value = plan }

const ejecutarEliminar = async () => {
  eliminando.value = true
  try {
    await api.delete(`/planes/${planAEliminar.value.id}`)
    planAEliminar.value = null
    await fetchPlanes()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al eliminar el plan.')
  } finally {
    eliminando.value = false
  }
}

onMounted(fetchPlanes)
</script>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.4s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
