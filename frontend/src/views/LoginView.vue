<template>
  <div class="min-h-screen flex items-center justify-center bg-black px-4 py-8">
    <div class="max-w-md w-full bg-white rounded-xl shadow-lg overflow-hidden relative">
      <!-- Barra superior roja -->
      <div class="absolute top-0 left-0 w-full h-2 bg-red-600"></div>

      <!-- Logo -->
      <div class="text-center pt-10 pb-6 px-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-red-100 text-red-600 mb-3 shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h1 class="text-2xl font-extrabold text-gray-800 tracking-tight">CrossFit Box</h1>
      </div>

      <!-- Tabs -->
      <div class="flex mx-8 mb-6 bg-gray-100 rounded-xl p-1">
        <button @click="tab = 'login'"
          class="flex-1 py-2 rounded-lg text-sm font-bold transition-all"
          :class="tab === 'login' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'">
          Iniciar Sesión
        </button>
        <button @click="tab = 'registro'"
          class="flex-1 py-2 rounded-lg text-sm font-bold transition-all"
          :class="tab === 'registro' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'">
          Registrarse
        </button>
      </div>

      <!-- ── FORMULARIO LOGIN ── -->
      <form v-if="tab === 'login'" @submit.prevent="handleLogin" class="px-8 pb-8 space-y-5">
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Correo Electrónico</label>
          <input v-model="loginEmail" type="email" required
            class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all text-sm"
            placeholder="ejemplo@correo.com">
        </div>
        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Contraseña</label>
          <input v-model="loginPassword" type="password" required
            class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all text-sm"
            placeholder="••••••••">
        </div>

        <div v-if="loginError" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg border border-red-100 flex items-start gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span class="font-medium">{{ loginError }}</span>
        </div>

        <button type="submit" :disabled="loginLoading"
          class="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-bold py-3 rounded-lg shadow-md transition-all flex items-center justify-center gap-2">
          <span v-if="loginLoading" class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
          {{ loginLoading ? 'Autenticando...' : 'Ingresar' }}
        </button>
      </form>

      <!-- ── FORMULARIO REGISTRO ── -->
      <form v-else @submit.prevent="handleRegistro" class="px-8 pb-8 space-y-4">

        <!-- Éxito de registro -->
        <div v-if="registroExitoso" class="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-emerald-500 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="font-bold text-emerald-800">¡Registro exitoso!</p>
          <p class="text-sm text-emerald-700 mt-1">Tu cuenta está pendiente de aprobación. Inicia sesión para ver los planes disponibles.</p>
          <button type="button" @click="tab = 'login'; registroExitoso = false"
            class="mt-3 text-sm font-semibold text-emerald-700 underline hover:text-emerald-900">
            Ir a iniciar sesión
          </button>
        </div>

        <template v-else>
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Nombre Completo <span class="text-red-500">*</span></label>
            <input v-model="regForm.nombre" type="text" required minlength="2" maxlength="120"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm"
              placeholder="Ej. Juan Pérez">
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Correo Electrónico <span class="text-red-500">*</span></label>
            <input v-model="regForm.email" type="email" required
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm"
              placeholder="ejemplo@correo.com">
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Documento de Identidad <span class="text-red-500">*</span></label>
            <input v-model="regForm.documento_identidad" type="text" required minlength="5" maxlength="20"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm"
              placeholder="Ej. 1020456789">
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Teléfono / WhatsApp <span class="text-red-500">*</span></label>
            <input v-model="regForm.telefono" type="tel" required minlength="7" maxlength="20"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm"
              placeholder="Ej. 3001234567">
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Género <span class="text-red-500">*</span></label>
            <select v-model="regForm.genero" required
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none appearance-none transition-all text-sm">
              <option value="" disabled>Selecciona...</option>
              <option value="masculino">Masculino</option>
              <option value="femenino">Femenino</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Contraseña <span class="text-red-500">*</span></label>
            <input v-model="regForm.password" type="password" required minlength="6"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm"
              placeholder="Mínimo 6 caracteres">
          </div>

          <div v-if="registroError" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg border border-red-100 flex items-start gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            <span class="font-medium">{{ registroError }}</span>
          </div>

          <button type="submit" :disabled="registroLoading"
            class="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white font-bold py-3 rounded-lg shadow-md transition-all flex items-center justify-center gap-2">
            <span v-if="registroLoading" class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
            {{ registroLoading ? 'Registrando...' : 'Crear Cuenta' }}
          </button>
        </template>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'
import { useRouter } from 'vue-router'

const router = useRouter()
const tab = ref('login')

// ── Login ──────────────────────────────────────────────────────
const loginEmail = ref('')
const loginPassword = ref('')
const loginError = ref('')
const loginLoading = ref(false)

const handleLogin = async () => {
  loginError.value = ''
  loginLoading.value = true
  try {
    const formData = new URLSearchParams()
    formData.append('username', loginEmail.value)
    formData.append('password', loginPassword.value)
    const { data } = await api.post('/login', formData)
    localStorage.setItem('token', data.access_token)

    const me = await api.get('/me')
    localStorage.setItem('userRol', me.data.rol)
    localStorage.setItem('userName', me.data.nombre)
    localStorage.setItem('fechaVencimiento', me.data.fecha_vencimiento || '')

    router.push('/')
  } catch (e) {
    loginError.value = e.response?.status === 401
      ? 'Credenciales incorrectas. Verifica tu email y contraseña.'
      : 'Error al conectar con el servidor.'
  } finally {
    loginLoading.value = false
  }
}

// ── Registro ───────────────────────────────────────────────────
const regForm = ref({ nombre: '', email: '', documento_identidad: '', telefono: '', genero: '', password: '' })
const registroError = ref('')
const registroLoading = ref(false)
const registroExitoso = ref(false)

const handleRegistro = async () => {
  registroError.value = ''
  registroLoading.value = true
  try {
    await api.post('/registro', regForm.value)
    registroExitoso.value = true
    regForm.value = { nombre: '', email: '', documento_identidad: '', telefono: '', genero: '', password: '' }
  } catch (e) {
    const d = e.response?.data?.detail
    registroError.value = Array.isArray(d) ? d[0].msg : (d || 'Error al registrar la cuenta.')
  } finally {
    registroLoading.value = false
  }
}
</script>
