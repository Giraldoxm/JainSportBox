<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 px-4">
    <div class="max-w-md w-full bg-white rounded-xl shadow-lg p-8 relative overflow-hidden">
      <!-- Decorador Superior -->
      <div class="absolute top-0 left-0 w-full h-2 bg-indigo-600"></div>
      
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 mb-4 shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-800">Iniciar Sesión</h2>
        <p class="text-sm text-gray-500 mt-2">Accede al panel de administración CrossFit Box</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">Correo Electrónico</label>
          <input 
            v-model="email" 
            type="email" 
            required 
            class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all placeholder-gray-400 font-medium" 
            placeholder="ejemplo@correo.com"
          >
        </div>
        
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-2">Contraseña</label>
          <input 
            v-model="password" 
            type="password" 
            required 
            class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all placeholder-gray-400 font-medium" 
            placeholder="••••••••"
          >
        </div>

        <div v-if="errorMsg" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg border border-red-100 flex items-start gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span class="font-medium">{{ errorMsg }}</span>
        </div>

        <button 
          type="submit" 
          :disabled="loading" 
          class="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-bold py-3 px-4 rounded-lg shadow-md transition-transform transform active:scale-95 flex items-center justify-center gap-2"
        >
          <span v-if="loading" class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
          {{ loading ? 'Autenticando...' : 'Ingresar al Panel' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)
const router = useRouter()

const handleLogin = async () => {
  errorMsg.value = ''
  loading.value = true
  
  try {
    // OAuth2PasswordRequestForm needs Form Data, not raw JSON
    const formData = new URLSearchParams()
    formData.append('username', email.value)
    formData.append('password', password.value)

    const response = await axios.post('http://127.0.0.1:8080/login', formData)
    
    // Almacenar el JWT localmente e ir al Dashboard
    localStorage.setItem('token', response.data.access_token)
    router.push('/')
  } catch (error) {
    console.error('Login error:', error)
    if (error.response?.status === 401) {
      errorMsg.value = 'Credenciales incorrectas. Verifica tu email y contraseña.'
    } else {
      errorMsg.value = 'Error al conectar con el servidor backend.'
    }
  } finally {
    loading.value = false
  }
}
</script>
