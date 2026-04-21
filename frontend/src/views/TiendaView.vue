<template>
  <div class="animate-fade-in-up">
    <div class="mb-8">
      <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Punto de Venta</h2>
      <p class="text-gray-500 mt-1">Vende productos del inventario directamente</p>
    </div>
    
    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
    </div>
    
    <div v-else-if="productos.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <div v-for="producto in productos" :key="producto.id" class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 group relative">
        <!-- Stock badge -->
        <div class="absolute top-3 right-3 z-10">
          <span :class="producto.stock > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" class="px-2.5 py-1 rounded-full text-xs font-bold shadow-sm backdrop-blur-md">
            Stock: {{ producto.stock }}
          </span>
        </div>
        
        <!-- Image placeholder -->
        <div class="h-48 bg-gradient-to-br from-indigo-50 to-blue-50 flex flex-col items-center justify-center p-6 border-b border-gray-100 group-hover:from-indigo-100 group-hover:to-blue-100 transition-colors">
          <div class="h-20 w-20 bg-white rounded-full flex items-center justify-center shadow-sm mb-3">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
          </div>
          <span class="text-indigo-900 font-bold text-center line-clamp-1">{{ producto.nombre }}</span>
        </div>
        
        <div class="p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-bold text-gray-800 line-clamp-1" :title="producto.nombre">{{ producto.nombre }}</h3>
            <p class="text-2xl font-black text-indigo-600">${{ producto.precio.toFixed(2) }}</p>
          </div>
          
          <p class="text-sm text-gray-500 mb-5 line-clamp-2 min-h-[40px]">{{ producto.descripcion || 'Sin descripción disponible.' }}</p>
          
          <button 
            @click="venderProducto(producto)"
            :disabled="producto.stock <= 0 || selling === producto.id"
            class="w-full py-3 px-4 rounded-xl font-bold text-sm tracking-wide uppercase transition-all duration-200 flex items-center justify-center gap-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            :class="producto.stock > 0 
              ? 'bg-indigo-600 hover:bg-indigo-700 text-white hover:shadow-md active:scale-95' 
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
          >
            <span v-if="selling === producto.id" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
            <svg v-else-if="producto.stock > 0" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            {{ selling === producto.id ? 'Procesando...' : (producto.stock > 0 ? 'Vender Producto' : 'Agotado') }}
          </button>
        </div>
      </div>
    </div>
    
    <div v-else class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-12 text-center text-gray-500 mt-6">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>
      <h3 class="text-xl font-bold text-gray-700 mb-2">No hay productos disponibles</h3>
      <p>Asegúrate de haber agregado productos al inventario en la base de datos.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const productos = ref([])
const loading = ref(true)
const selling = ref(null)

const fetchProductos = async () => {
  loading.value = true
  try {
    const response = await api.get('/productos/')
    productos.value = response.data
  } catch (error) {
    console.error('Error fetching inventory:', error)
  } finally {
    loading.value = false
  }
}

const venderProducto = async (producto) => {
  selling.value = producto.id
  try {
    await api.post('/ventas/', {
      producto_id: producto.id,
      cantidad: 1
    })
    
    const index = productos.value.findIndex(p => p.id === producto.id);
    if(index !== -1) {
      productos.value[index].stock -= 1;
    }
    
  } catch (error) {
    console.error('Error processing sale:', error)
    alert('Error al registrar venta. Revisa la consola o asegúrate que el backend corre.')
  } finally {
    selling.value = null
  }
}

onMounted(() => {
  fetchProductos()
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
