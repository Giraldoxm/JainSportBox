<template>
  <div class="flex h-screen bg-gray-50 font-sans">
    <!-- Sidebar -->
    <aside class="w-64 bg-black text-white flex flex-col shadow-xl">
      <div class="p-6 border-b border-gray-800 flex items-center gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h1 class="text-xl font-extrabold tracking-wider">CrossFit Box</h1>
      </div>

      <!-- User info -->
      <div class="px-4 py-4 border-b border-gray-800">
        <p class="text-sm font-semibold text-white truncate">{{ nombre }}</p>
        <span class="inline-block mt-1 text-xs font-bold px-2 py-0.5 rounded-full"
          :class="{
            'bg-red-500 text-white': isAdmin,
            'bg-emerald-500 text-white': isCoach,
            'bg-gray-600 text-gray-200': isCliente,
          }">
          {{ rolLabel }}
        </span>
      </div>

      <nav class="flex-1 mt-4 px-4 space-y-2">
        <!-- Admin & Coach only -->
        <template v-if="canManage">
          <router-link to="/usuarios" class="flex items-center gap-3 py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors" active-class="bg-red-600 hover:bg-red-700 font-semibold shadow-md">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            Usuarios
          </router-link>
          <router-link to="/tienda" class="flex items-center gap-3 py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors" active-class="bg-red-600 hover:bg-red-700 font-semibold shadow-md">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
            Tienda POS
          </router-link>
          <router-link to="/alertas" class="flex items-center gap-3 py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors" active-class="bg-red-600 hover:bg-red-700 font-semibold shadow-md">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            Alertas WhatsApp
            <span v-if="alertasPendientes > 0"
              class="ml-auto bg-red-500 text-white text-xs font-black px-1.5 py-0.5 rounded-full min-w-[20px] text-center">
              {{ alertasPendientes }}
            </span>
          </router-link>
        </template>

        <!-- Admin only: Finanzas -->
        <template v-if="isAdmin">
          <div class="pt-2 pb-1 px-2">
            <p class="text-xs font-bold text-gray-500 uppercase tracking-widest">Administración</p>
          </div>
          <router-link to="/finanzas" class="flex items-center gap-3 py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors" active-class="bg-red-600 hover:bg-red-700 font-semibold shadow-md">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Finanzas
          </router-link>
        </template>

        <!-- Todos los roles -->
        <div class="pt-2 pb-1 px-2" v-if="canManage">
          <p class="text-xs font-bold text-gray-500 uppercase tracking-widest">Operaciones</p>
        </div>
        <router-link to="/wods" class="flex items-center gap-3 py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors" active-class="bg-red-600 hover:bg-red-700 font-semibold shadow-md">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          WODs
        </router-link>
        <router-link v-if="isCliente" to="/tienda" class="flex items-center gap-3 py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors" active-class="bg-red-600 hover:bg-red-700 font-semibold shadow-md">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
          Tienda
        </router-link>
        <router-link v-if="isCliente" to="/salud" class="flex items-center gap-3 py-3 px-4 rounded-lg hover:bg-gray-800 transition-colors" active-class="bg-red-600 hover:bg-red-700 font-semibold shadow-md">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
          Mi Salud
        </router-link>
      </nav>

      <div class="p-4 border-t border-gray-800">
        <button
          @click="logout"
          class="w-full flex items-center gap-3 py-3 px-4 rounded-lg text-gray-400 hover:bg-red-600 hover:text-white transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span class="font-semibold text-sm">Cerrar Sesión</span>
        </button>
        <p class="text-xs text-gray-600 text-center mt-3">&copy; 2026 CrossFit Box</p>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-x-hidden overflow-y-auto">
      <div class="p-8">
        <router-view></router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import api from '../api'

const router = useRouter()
const { nombre, rol, isAdmin, isCoach, isCliente, canManage } = useAuth()

const alertasPendientes = ref(0)

async function cargarConteoAlertas() {
  if (!canManage.value) return
  try {
    const { data } = await api.get('/alertas/contar')
    alertasPendientes.value = data.pendientes
  } catch { /* silencioso */ }
}

onMounted(cargarConteoAlertas)

const rolLabel = computed(() => {
  const labels = { admin: 'Administrador', coach: 'Coach', cliente: 'Cliente' }
  return labels[rol.value] || rol.value
})

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('userRol')
  localStorage.removeItem('userName')
  router.push('/login')
}
</script>
