<template>
  <div class="animate-fade-in-up">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
      <div>
        <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Clientes</h2>
        <p class="text-gray-500 mt-1">Gestiona los usuarios y sus membresías</p>
      </div>
      <button @click="showForm = true" class="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all font-semibold flex items-center gap-2 transform active:scale-95">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
        </svg>
        Nuevo Usuario
      </button>
    </div>

    <!-- Table Card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Nombre</th>
              <th scope="col" class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Rol</th>
              <th scope="col" class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Plan</th>
              <th scope="col" class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Estado en Gym</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-100">
            <tr v-for="user in usuarios" :key="user.id" class="hover:bg-gray-50 transition-colors group">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="h-10 w-10 flex-shrink-0">
                    <img class="h-10 w-10 rounded-full bg-gray-100" :src="'https://ui-avatars.com/api/?name=' + user.nombre + '&background=random'" alt="" />
                  </div>
                  <div class="ml-4">
                    <div class="text-sm font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">{{ user.nombre }}</div>
                    <div class="text-sm text-gray-500">ID Huella: {{ user.huella_id || 'N/D' }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                  {{ user.rol }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ user.plan_id ? 'Membresía Activa' : 'Sin Plan' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="user.esta_en_gym ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-gray-100 text-gray-600 border border-gray-200'" class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full shadow-sm">
                  <span v-if="user.esta_en_gym" class="w-2 h-2 rounded-full bg-green-500 mr-1.5 mt-1"></span>
                  {{ user.esta_en_gym ? 'En el Box' : 'Fuera' }}
                </span>
              </td>
            </tr>
            <tr v-if="usuarios.length === 0 && !loading">
              <td colspan="4" class="px-6 py-12 text-center text-gray-500 bg-gray-50 rounded-b-xl border-t border-gray-200 border-dashed">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                No hay usuarios registrados.
              </td>
            </tr>
            <tr v-if="loading">
              <td colspan="4" class="px-6 py-12 text-center">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Form -->
    <div v-if="showForm" class="fixed inset-0 flex items-center justify-center bg-gray-900 bg-opacity-60 backdrop-blur-sm z-50 transition-opacity">
      <div class="bg-white rounded-2xl p-8 w-full max-w-md shadow-2xl transform transition-all scale-100">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-2xl font-bold text-gray-900">Registrar Usuario</h3>
          <button @click="showForm = false" class="text-gray-400 hover:text-gray-600 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form @submit.prevent="crearUsuario">
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Nombre Completo</label>
            <input v-model="nuevoUsuario.nombre" type="text" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="Ej. Juan Pérez" required>
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Email</label>
            <input v-model="nuevoUsuario.email" type="email" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="Ej. juan@correo.com" required>
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Contraseña</label>
            <input v-model="nuevoUsuario.password" type="password" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all" placeholder="Min. 6 caracteres" required minlength="6">
          </div>
          <div class="mb-6">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Rol del Usuario</label>
            <div class="relative">
              <select v-model="nuevoUsuario.rol" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none appearance-none transition-all">
                <option value="cliente">Cliente</option>
                <option value="coach">Coach</option>
                <option value="admin">Admin</option>
              </select>
              <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-500">
                <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
              </div>
            </div>
          </div>
          <div class="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button @click="showForm = false" type="button" class="px-5 py-2.5 rounded-lg text-gray-600 font-semibold hover:bg-gray-100 transition-colors">
              Cancelar
            </button>
            <button type="submit" class="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-md inline-flex items-center gap-2 transition-all transform active:scale-95" :disabled="saving">
              <span v-if="saving" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ saving ? 'Guardando...' : 'Guardar Usuario' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const usuarios = ref([])
const showForm = ref(false)
const loading = ref(true)
const saving = ref(false)

const nuevoUsuario = ref({
  nombre: '',
  email: '',
  password: '',
  rol: 'cliente'
})

const fetchUsuarios = async () => {
  loading.value = true
  try {
    const response = await axios.get('http://127.0.0.1:8080/usuarios/')
    usuarios.value = response.data
  } catch (error) {
    console.error('Error fetching users:', error)
  } finally {
    loading.value = false
  }
}

const crearUsuario = async () => {
  saving.value = true
  try {
    await axios.post('http://127.0.0.1:8080/usuarios/', nuevoUsuario.value)
    showForm.value = false
    nuevoUsuario.value = { nombre: '', email: '', password: '', rol: 'cliente' }
    await fetchUsuarios()
  } catch (error) {
    console.error('Error creating user:', error)
    const errDetail = error.response?.data?.detail;
    const msg = Array.isArray(errDetail) ? errDetail[0].msg : (errDetail || error.message);
    alert('Error al crear usuario: ' + msg);
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchUsuarios()
})
</script>

<style>
.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
