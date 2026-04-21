<template>
  <div class="animate-fade-in-up">
    <div class="mb-8">
      <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Monitor de Acceso</h2>
      <p class="text-gray-500 mt-1">Busca un socio y valida su estatus para registrar entrada</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Columna Izquierda: Buscador de Usuarios -->
      <div class="col-span-1 lg:col-span-1 bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex flex-col h-[600px]">
        <h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
          </svg>
          Buscar Miembro
        </h3>
        
        <div class="mb-4">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="Escribe el nombre o ID..." 
            class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none transition-all shadow-inner"
          >
        </div>

        <div v-if="loading" class="flex-1 flex items-center justify-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
        </div>

        <ul v-else class="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
          <li v-if="filteredUsers.length === 0" class="text-center text-gray-400 py-8 italic">
            No se encontraron usuarios
          </li>
          <li 
            v-for="user in filteredUsers" 
            :key="user.id" 
            @click="selectUser(user)"
            class="p-3 rounded-xl border transition-all cursor-pointer flex items-center gap-3 hover:bg-red-50"
            :class="selectedUser?.id === user.id ? 'border-red-500 bg-red-50 ring-1 ring-red-500' : 'border-gray-100 bg-white'"
          >
            <img class="h-10 w-10 rounded-full bg-gray-200" :src="'https://ui-avatars.com/api/?name=' + user.nombre + '&background=random'" alt="Avatar" />
            <div class="flex-1 min-w-0">
              <p class="text-sm font-bold text-gray-900 truncate">{{ user.nombre }}</p>
              <p class="text-xs text-gray-500 truncate">ID: {{ user.id }}</p>
            </div>
            <div>
              <span v-if="isVigenteCheck(user)" class="w-3 h-3 bg-green-500 rounded-full inline-block shadow-sm"></span>
              <span v-else class="w-3 h-3 bg-red-500 rounded-full inline-block shadow-sm"></span>
            </div>
          </li>
        </ul>
      </div>

      <!-- Columna Derecha: Tarjeta de Acceso -->
      <div class="col-span-1 lg:col-span-2">
        <div v-if="!selectedUser" class="h-full bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 flex flex-col items-center justify-center p-12 text-center text-gray-400 transition-all">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-20 w-20 mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
          </svg>
          <p class="text-xl font-semibold">Selecciona un usuario a la izquierda</p>
          <p class="mt-2 text-sm">Validaremos su estado automáticamente antes de permitir el acceso.</p>
        </div>

        <div v-else class="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden transform transition-all relative">
          
          <div :class="isVigente ? 'bg-green-500' : 'bg-red-500'" class="h-32 absolute top-0 left-0 w-full transition-colors z-0"></div>
          
          <div class="relative z-10 px-8 pt-20 pb-8 flex flex-col items-center">
            <img class="h-32 w-32 rounded-full border-4 border-white shadow-xl bg-white" :src="'https://ui-avatars.com/api/?name=' + selectedUser.nombre + '&background=random&size=200'" alt="Avatar Grande" />
            
            <h2 class="text-3xl font-black text-gray-900 mt-4 text-center">{{ selectedUser.nombre }}</h2>
            <p class="text-gray-500 font-medium">Cliente ID: #{{ selectedUser.id }}</p>

            <div class="mt-6 w-full">
              <div 
                :class="isVigente ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'"
                class="border-2 rounded-xl p-6 text-center shadow-inner transition-colors"
              >
                <p class="text-xs uppercase tracking-widest font-bold mb-1 opacity-70">Estado de Membresía</p>
                <p class="text-4xl font-black tracking-tight" :class="isVigente ? 'text-green-600' : 'text-red-600'">
                  {{ isVigente ? 'VIGENTE' : 'VENCIDA' }}
                </p>
                <div class="mt-3 flex items-center justify-center gap-2 font-medium">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Vencimiento: {{ selectedUser.fecha_vencimiento ? selectedUser.fecha_vencimiento : 'Nunca registrado' }}
                </div>
              </div>
            </div>

            <div class="mt-8 w-full border-t border-gray-100 pt-8">
              <button 
                @click="registrarEntrada"
                :disabled="!isVigente || recording"
                class="w-full py-4 text-lg rounded-xl font-bold uppercase tracking-wider transition-all transform flex justify-center items-center gap-3 shadow-lg disabled:shadow-none"
                :class="isVigente 
                  ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white active:scale-95' 
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
              >
                <span v-if="recording" class="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></span>
                <span v-else-if="isVigente">Validar Acceso</span>
                <span v-else>Acceso Denegado</span>
                
                <svg v-if="!recording && isVigente" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
                <svg v-else-if="!isVigente" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const users = ref([])
const loading = ref(true)
const searchQuery = ref('')
const selectedUser = ref(null)
const recording = ref(false)

const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await axios.get('http://127.0.0.1:8080/usuarios/')
    users.value = response.data
  } catch (error) {
    console.error("Error fetching users for monitor:", error)
  } finally {
    loading.value = false
  }
}

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(u => 
    u.nombre.toLowerCase().includes(query) || 
    u.id.toString().includes(query)
  )
})

const selectUser = (user) => {
  selectedUser.value = user
}

// Logic to check validity natively on UI to display colors
const isVigenteCheck = (user) => {
  // Staff (Admin/Coach) siempre están vigentes
  if (user.rol === 'admin' || user.rol === 'coach') return true
  
  if (!user.fecha_vencimiento) return false
  
  // Parsear la fecha manual asegurando la zona local ("YYYY-MM-DD")
  const partes = user.fecha_vencimiento.split('-')
  if (partes.length !== 3) return false
  const vencimiento = new Date(partes[0], partes[1] - 1, partes[2])
  
  const hoy = new Date()
  
  // Set times to midnight to only compare dates properly
  vencimiento.setHours(0,0,0,0)
  hoy.setHours(0,0,0,0)
  
  return vencimiento >= hoy
}

const isVigente = computed(() => {
  if (!selectedUser.value) return false
  return isVigenteCheck(selectedUser.value)
})

const registrarEntrada = async () => {
  if (!selectedUser.value) return
  recording.value = true
  try {
    const response = await axios.post('http://127.0.0.1:8080/asistencias/', {
      usuario_id: selectedUser.value.id
    })
    alert('Entrada exitosa: ' + response.data.message)
    // Clear selection or update UI
    selectedUser.value = null
    searchQuery.value = ''
  } catch (error) {
    console.error('Error logging access:', error)
    if(error.response?.status === 403) {
      alert('SERVIDOR BLOQUEADO: Membresía Vencida o Inactiva')
    } else {
      alert('Error de Servidor verificando asistencia')
    }
  } finally {
    recording.value = false
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
