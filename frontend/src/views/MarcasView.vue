<template>
  <div class="animate-fade-in-up">

    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Mis Marcas</h2>
      <p class="text-gray-500 mt-1">Récords personales · Selecciona un ejercicio para ver y registrar tu 1RM</p>
    </div>

    <!-- Skeletons -->
    <div v-if="cargando" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <div v-for="i in 12" :key="i" class="bg-gray-100 rounded-2xl h-28 animate-pulse"></div>
    </div>

    <!-- Grid fijo de ejercicios -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <RouterLink
        v-for="nombre in EJERCICIOS_MARCAS"
        :key="nombre"
        :to="{ name: 'MarcasEjercicio', params: { ejercicio: nombre } }"
        class="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow group overflow-hidden">

        <!-- Valor del PR -->
        <div class="px-5 pt-5 pb-3">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <p class="text-xs font-bold uppercase tracking-widest text-gray-400 mb-1">Mejor 1RM</p>
              <template v-if="prDe(nombre)">
                <p class="text-3xl font-black text-gray-900 leading-none">
                  {{ prDe(nombre).rm }}<span class="text-base font-semibold text-gray-400 ml-1">{{ prDe(nombre).unidad }}</span>
                </p>
                <p class="text-xs text-gray-400 mt-1">{{ conteo(nombre) }} registro{{ conteo(nombre) !== 1 ? 's' : '' }}</p>
              </template>
              <template v-else>
                <p class="text-2xl font-black text-gray-300">Sin registros</p>
                <p class="text-xs text-gray-400 mt-1">Toca para empezar</p>
              </template>
            </div>
            <svg xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 text-gray-300 group-hover:text-gray-500 group-hover:translate-x-0.5 transition-all shrink-0 mt-1"
              fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </div>
        </div>

        <!-- Nombre del ejercicio -->
        <div class="px-5 py-3 border-t border-gray-50">
          <p class="font-bold text-gray-800">{{ nombre }}</p>
        </div>

      </RouterLink>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'
import { EJERCICIOS_MARCAS } from '../data/ejerciciosMarcas'

const marcas   = ref([])
const cargando = ref(true)

function prDe(nombre) {
  const lista = marcas.value.filter(m => m.ejercicio === nombre)
  if (!lista.length) return null
  const mejor = lista.reduce((a, b) => b.rm_calculado > a.rm_calculado ? b : a)
  return { rm: mejor.rm_calculado, unidad: mejor.unidad }
}

function conteo(nombre) {
  return marcas.value.filter(m => m.ejercicio === nombre).length
}

async function cargar() {
  cargando.value = true
  try {
    const { data } = await api.get('/marcas/')
    marcas.value = data
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)
</script>

<style scoped>
.animate-fade-in-up { animation: fadeInUp 0.4s ease-out; }
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
