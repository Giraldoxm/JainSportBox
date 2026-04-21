<template>
  <div class="animate-fade-in-up">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
      <div>
        <h2 class="text-3xl font-extrabold text-gray-900 tracking-tight">Usuarios</h2>
        <p class="text-gray-500 mt-1">Gestiona los usuarios y sus membresías</p>
      </div>
      <button @click="showForm = true" class="bg-red-600 hover:bg-red-700 text-white px-5 py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all font-semibold flex items-center gap-2 transform active:scale-95">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
        </svg>
        Nuevo Usuario
      </button>
    </div>

    <!-- Filtros -->
    <div class="flex flex-wrap gap-2 mb-5">
      <button v-for="tab in tabs" :key="tab.key" @click="filtroActivo = tab.key"
        class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all border"
        :class="filtroActivo === tab.key
          ? 'bg-red-600 text-white border-red-600 shadow-md'
          : 'bg-white text-gray-600 border-gray-200 hover:border-red-300 hover:text-red-600'">
        {{ tab.label }}
        <span class="text-xs font-black px-1.5 py-0.5 rounded-full"
          :class="filtroActivo === tab.key ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-500'">
          {{ tab.count }}
        </span>
      </button>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Usuario</th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Rol</th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Membresía</th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Estado</th>
              <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-100">
            <tr v-for="user in usuariosFiltrados" :key="user.id" class="hover:bg-gray-50 transition-colors group">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center gap-3">
                  <img class="h-10 w-10 rounded-full object-cover bg-gray-100 flex-shrink-0" :src="fotoSrc(user)" alt="" />
                  <div>
                    <div class="text-sm font-semibold text-gray-900 group-hover:text-red-600 transition-colors">{{ user.nombre }}</div>
                    <div class="text-xs text-gray-500">{{ user.email }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                  :class="{
                    'bg-purple-100 text-purple-800': user.rol === 'admin',
                    'bg-blue-100 text-blue-800': user.rol === 'coach',
                    'bg-gray-100 text-gray-700': user.rol === 'cliente',
                  }">
                  {{ user.rol }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <template v-if="user.fecha_vencimiento">
                  <div class="flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full flex-shrink-0"
                      :class="colorPuntoDias(diasRestantes(user.fecha_vencimiento))"></span>
                    <div>
                      <p class="text-sm font-semibold" :class="colorTextoDias(diasRestantes(user.fecha_vencimiento))">
                        {{ etiquetaDias(diasRestantes(user.fecha_vencimiento)) }}
                      </p>
                      <p class="text-xs text-gray-400">Vence {{ formatFecha(user.fecha_vencimiento) }}</p>
                    </div>
                  </div>
                </template>
                <span v-else class="text-sm text-gray-400 italic">Sin membresía</span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-3 py-1 inline-flex items-center gap-1.5 text-xs font-semibold rounded-full border shadow-sm"
                  :class="user.esta_en_gym ? 'bg-green-100 text-green-800 border-green-200' : 'bg-gray-100 text-gray-600 border-gray-200'">
                  <span class="w-2 h-2 rounded-full" :class="user.esta_en_gym ? 'bg-green-500' : 'bg-gray-400'"></span>
                  {{ user.esta_en_gym ? 'En el Box' : 'Fuera' }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center gap-2">
                  <button @click="verUsuario(user)" title="Ver detalle"
                    class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                  </button>
                  <button @click="confirmarEliminar(user)" title="Eliminar"
                    class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="usuariosFiltrados.length === 0 && !loading">
              <td colspan="5" class="px-6 py-12 text-center text-gray-400 bg-gray-50">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                {{ tabs.find(t => t.key === filtroActivo)?.emptyMsg || 'No hay usuarios.' }}
              </td>
            </tr>
            <tr v-if="loading">
              <td colspan="5" class="px-6 py-12 text-center">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto"></div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Modal: Ver detalle ── -->
    <div v-if="usuarioSeleccionado" class="fixed inset-0 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden">
        <div class="bg-gradient-to-r from-red-600 to-red-700 px-8 py-6 flex items-center gap-4">
          <img class="h-16 w-16 rounded-full border-4 border-white shadow-md object-cover" :src="fotoSrc(usuarioSeleccionado, 128)" alt="" />
          <div>
            <h3 class="text-xl font-bold text-white">{{ usuarioSeleccionado.nombre }}</h3>
            <span class="inline-block mt-1 px-2.5 py-0.5 text-xs font-semibold bg-white/20 text-white rounded-full">{{ usuarioSeleccionado.rol }}</span>
          </div>
          <button @click="usuarioSeleccionado = null" class="ml-auto text-white/70 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="px-8 py-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Email</p>
              <p class="text-sm font-semibold text-gray-800 break-all">{{ usuarioSeleccionado.email }}</p>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">ID Huella</p>
              <p class="text-sm font-semibold text-gray-800">{{ usuarioSeleccionado.huella_id || 'No registrada' }}</p>
            </div>
            <div class="bg-gray-50 rounded-xl p-4 col-span-2">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-2">Membresía</p>
              <template v-if="usuarioSeleccionado.fecha_vencimiento">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-bold" :class="colorTextoDias(diasRestantes(usuarioSeleccionado.fecha_vencimiento))">
                      {{ etiquetaDias(diasRestantes(usuarioSeleccionado.fecha_vencimiento)) }}
                    </p>
                    <p class="text-xs text-gray-500 mt-0.5">Vence el {{ formatFecha(usuarioSeleccionado.fecha_vencimiento) }}</p>
                  </div>
                  <div class="w-12 h-12 rounded-full flex items-center justify-center"
                    :class="bgCirculoDias(diasRestantes(usuarioSeleccionado.fecha_vencimiento))">
                    <span class="text-xs font-black" :class="colorTextoDias(diasRestantes(usuarioSeleccionado.fecha_vencimiento))">
                      {{ Math.abs(diasRestantes(usuarioSeleccionado.fecha_vencimiento)) }}d
                    </span>
                  </div>
                </div>
              </template>
              <p v-else class="text-sm text-gray-400">Sin membresía activa</p>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">En el box</p>
              <div class="flex items-center gap-2 mt-1">
                <span class="w-2.5 h-2.5 rounded-full" :class="usuarioSeleccionado.esta_en_gym ? 'bg-green-500' : 'bg-gray-300'"></span>
                <p class="text-sm font-semibold text-gray-800">{{ usuarioSeleccionado.esta_en_gym ? 'En el Box' : 'Fuera' }}</p>
              </div>
            </div>
            <div class="bg-gray-50 rounded-xl p-4">
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Miembro desde</p>
              <p class="text-sm font-semibold text-gray-800">{{ formatFechaCorta(usuarioSeleccionado.created_at) }}</p>
            </div>
          </div>
        </div>
        <div class="px-8 pb-6 flex gap-3">
          <button @click="usuarioSeleccionado = null" class="py-2.5 px-4 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">Cerrar</button>
          <button @click="abrirRenovar(usuarioSeleccionado); usuarioSeleccionado = null" class="flex-1 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold transition-colors">Renovar</button>
          <button @click="abrirEditar(usuarioSeleccionado); usuarioSeleccionado = null" class="flex-1 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-semibold transition-colors">Editar</button>
        </div>
      </div>
    </div>

    <!-- ── Modal: Renovar membresía ── -->
    <div v-if="showRenovar" class="fixed inset-0 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-lg shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <div class="bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-5 flex items-center gap-3 flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          <div>
            <h3 class="text-lg font-bold text-white">Renovar Membresía</h3>
            <p class="text-emerald-100 text-sm">{{ renovarUsuario?.nombre }}</p>
          </div>
          <button @click="showRenovar = false" class="ml-auto text-white/70 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="px-6 py-5 overflow-y-auto flex-1">
          <!-- Estado actual -->
          <div class="mb-5 p-3 rounded-xl"
            :class="renovarUsuario?.fecha_vencimiento && diasRestantes(renovarUsuario.fecha_vencimiento) > 0
              ? 'bg-emerald-50 border border-emerald-100'
              : 'bg-red-50 border border-red-100'">
            <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Membresía actual</p>
            <template v-if="renovarUsuario?.fecha_vencimiento">
              <p class="text-sm font-bold" :class="colorTextoDias(diasRestantes(renovarUsuario.fecha_vencimiento))">
                {{ etiquetaDias(diasRestantes(renovarUsuario.fecha_vencimiento)) }}
              </p>
              <p class="text-xs text-gray-500">Vence el {{ formatFecha(renovarUsuario.fecha_vencimiento) }} · Los días nuevos se sumarán a esa fecha.</p>
            </template>
            <p v-else class="text-sm text-gray-500">Sin membresía activa — los días contarán desde hoy.</p>
          </div>

          <!-- Selección de plan -->
          <p class="text-sm font-semibold text-gray-700 mb-3">Selecciona un plan</p>
          <div class="grid grid-cols-2 gap-3 mb-4">
            <label v-for="plan in planes" :key="plan.id"
              class="flex flex-col items-center p-4 rounded-xl border-2 cursor-pointer transition-all"
              :class="renovarPlan === plan.id ? 'border-emerald-500 bg-emerald-50' : 'border-gray-200 hover:border-gray-300'">
              <input type="radio" v-model="renovarPlan" :value="plan.id" class="sr-only">
              <span class="text-2xl font-black mb-0.5" :class="renovarPlan === plan.id ? 'text-emerald-600' : 'text-gray-700'">
                {{ plan.duracion_dias }}<span class="text-sm font-bold">d</span>
              </span>
              <span class="text-sm font-bold" :class="renovarPlan === plan.id ? 'text-emerald-700' : 'text-gray-600'">{{ plan.nombre }}</span>
              <span class="text-xs mt-1" :class="renovarPlan === plan.id ? 'text-emerald-500' : 'text-gray-400'">${{ plan.precio.toLocaleString() }}</span>
            </label>

            <label class="flex flex-col items-center p-4 rounded-xl border-2 cursor-pointer transition-all col-span-2"
              :class="renovarPlan === 'personalizado' ? 'border-emerald-500 bg-emerald-50' : 'border-gray-200 hover:border-gray-300'">
              <input type="radio" v-model="renovarPlan" value="personalizado" class="sr-only">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mb-1" :class="renovarPlan === 'personalizado' ? 'text-emerald-500' : 'text-gray-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
              <span class="text-sm font-bold" :class="renovarPlan === 'personalizado' ? 'text-emerald-700' : 'text-gray-600'">Personalizado (días)</span>
            </label>
          </div>

          <!-- Días personalizados -->
          <div v-if="renovarPlan === 'personalizado'" class="mb-4">
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Días a agregar</label>
            <input v-model.number="renovarDias" type="number" min="1" max="365"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 outline-none"
              placeholder="Ej: 10">
          </div>

          <!-- Monto -->
          <div class="mb-4">
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">
              Monto cobrado ($)
              <span v-if="renovarPlan !== 'personalizado' && planSeleccionadoObj" class="text-gray-400 font-normal">
                — sugerido ${{ planSeleccionadoObj.precio.toLocaleString() }}
              </span>
            </label>
            <input v-model.number="renovarMonto" type="number" min="0" step="any"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-emerald-500 outline-none"
              :placeholder="planSeleccionadoObj ? '$' + planSeleccionadoObj.precio.toLocaleString() : 'Ej: 100000'">
          </div>

          <!-- Método de pago -->
          <div class="mb-5">
            <label class="block text-sm font-semibold text-gray-700 mb-1.5">Método de pago</label>
            <div class="grid grid-cols-3 gap-2">
              <label v-for="m in metodos" :key="m.value"
                class="flex items-center justify-center gap-1.5 p-2.5 rounded-lg border-2 cursor-pointer transition-all text-sm font-semibold"
                :class="renovarMetodo === m.value ? 'border-emerald-500 bg-emerald-50 text-emerald-700' : 'border-gray-200 text-gray-600 hover:border-gray-300'">
                <input type="radio" v-model="renovarMetodo" :value="m.value" class="sr-only">
                {{ m.label }}
              </label>
            </div>
          </div>

          <div v-if="errorRenovar" class="mb-4 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg p-3">{{ errorRenovar }}</div>

          <div class="flex gap-3">
            <button @click="showRenovar = false" class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">Cancelar</button>
            <button @click="confirmarRenovacion" :disabled="guardandoRenovar || !renovarPlan"
              class="flex-1 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold transition-colors disabled:bg-emerald-200 flex items-center justify-center gap-2">
              <span v-if="guardandoRenovar" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ guardandoRenovar ? 'Guardando...' : 'Confirmar Renovación' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Modal: Editar usuario ── -->
    <div v-if="showEditar" class="fixed inset-0 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-6">
          <div>
            <h3 class="text-2xl font-bold text-gray-900">Editar Usuario</h3>
            <p class="text-sm text-gray-500 mt-0.5">{{ editando?.nombre }}</p>
          </div>
          <button @click="cerrarEditar" class="text-gray-400 hover:text-gray-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- Foto -->
        <div class="mb-6 flex flex-col items-center">
          <div class="relative h-24 w-24 rounded-full border-4 border-dashed border-gray-200 bg-gray-50 flex items-center justify-center cursor-pointer hover:border-red-400 hover:bg-red-50 transition-all overflow-hidden"
            @click="$refs.inputFotoEdit.click()">
            <img v-if="editFotoPreview" :src="editFotoPreview" class="h-full w-full object-cover" />
            <img v-else-if="editando?.foto_url" :src="'http://127.0.0.1:8000' + editando.foto_url" class="h-full w-full object-cover" />
            <div v-else class="flex flex-col items-center text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            </div>
            <input ref="inputFotoEdit" type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onFotoEditChange" />
          </div>
          <p class="text-xs text-gray-400 mt-2">Clic para cambiar la foto</p>
        </div>

        <form @submit.prevent="guardarEdicion">
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Email</label>
            <input v-model="editForm.email" type="email" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" required>
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Teléfono / WhatsApp</label>
            <input v-model="editForm.telefono" type="tel" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" placeholder="Ej. 3001234567">
          </div>
          <div class="mb-6">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Nueva Contraseña <span class="text-gray-400 font-normal">(dejar vacío para no cambiar)</span></label>
            <input v-model="editForm.password" type="password" minlength="6" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" placeholder="Min. 6 caracteres">
          </div>
          <div class="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button @click="cerrarEditar" type="button" class="px-5 py-2.5 rounded-lg text-gray-600 font-semibold hover:bg-gray-100 transition-colors">Cancelar</button>
            <button type="submit" :disabled="guardandoEdicion" class="px-5 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold shadow-md inline-flex items-center gap-2 transition-all active:scale-95">
              <span v-if="guardandoEdicion" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ guardandoEdicion ? 'Guardando...' : 'Guardar Cambios' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ── Modal: Crear usuario ── -->
    <div v-if="showForm" class="fixed inset-0 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl p-8 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-2xl font-bold text-gray-900">Registrar Usuario</h3>
          <button @click="cerrarFormulario" class="text-gray-400 hover:text-gray-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- Foto -->
        <div class="mb-6 flex flex-col items-center">
          <div class="relative h-24 w-24 rounded-full border-4 border-dashed border-gray-200 bg-gray-50 flex items-center justify-center cursor-pointer hover:border-red-400 hover:bg-red-50 transition-all overflow-hidden"
            @click="$refs.inputFoto.click()">
            <img v-if="fotoPreview" :src="fotoPreview" class="h-full w-full object-cover" />
            <div v-else class="flex flex-col items-center text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            </div>
            <input ref="inputFoto" type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onFotoChange" />
          </div>
          <p class="text-xs text-gray-400 mt-2">Foto de perfil (opcional)</p>
          <button v-if="fotoArchivo" type="button" @click="quitarFoto" class="text-xs text-red-400 hover:text-red-600 mt-1">Quitar foto</button>
        </div>

        <form @submit.prevent="crearUsuario">
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Nombre Completo</label>
            <input v-model="nuevoUsuario.nombre" type="text" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" placeholder="Ej. Juan Pérez" required>
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Email</label>
            <input v-model="nuevoUsuario.email" type="email" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" placeholder="Ej. juan@correo.com" required>
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Contraseña</label>
            <input v-model="nuevoUsuario.password" type="password" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" placeholder="Min. 6 caracteres" required minlength="6">
          </div>
          <div class="mb-5">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Teléfono / WhatsApp <span class="text-red-500">*</span></label>
            <input v-model="nuevoUsuario.telefono" type="tel" required minlength="7" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none transition-all" placeholder="Ej. 3001234567">
          </div>
          <div class="mb-6">
            <label class="block text-gray-700 text-sm font-semibold mb-2">Rol</label>
            <select v-model="nuevoUsuario.rol" class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none appearance-none transition-all">
              <option value="cliente">Cliente</option>
              <option value="coach">Coach</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <!-- Plan inicial -->
          <div class="border-t border-gray-100 pt-5 mb-6">
            <label class="block text-gray-700 text-sm font-semibold mb-3">Plan de Membresía <span class="text-gray-400 font-normal">(opcional)</span></label>
            <div class="grid grid-cols-2 gap-3">
              <label class="flex flex-col items-center p-3 rounded-xl border-2 cursor-pointer transition-all"
                :class="planSeleccionado === 'ninguno' ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'">
                <input type="radio" v-model="planSeleccionado" value="ninguno" class="sr-only">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mb-1" :class="planSeleccionado === 'ninguno' ? 'text-red-400' : 'text-gray-300'" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/></svg>
                <span class="text-xs font-semibold" :class="planSeleccionado === 'ninguno' ? 'text-red-700' : 'text-gray-500'">Sin plan</span>
              </label>
              <label v-for="plan in planes" :key="plan.id"
                class="flex flex-col items-center p-3 rounded-xl border-2 cursor-pointer transition-all"
                :class="planSeleccionado === plan.id ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'">
                <input type="radio" v-model="planSeleccionado" :value="plan.id" class="sr-only">
                <span class="text-lg font-black" :class="planSeleccionado === plan.id ? 'text-red-600' : 'text-gray-700'">{{ plan.duracion_dias }}d</span>
                <span class="text-xs font-semibold" :class="planSeleccionado === plan.id ? 'text-red-700' : 'text-gray-600'">{{ plan.nombre }}</span>
                <span class="text-xs mt-0.5" :class="planSeleccionado === plan.id ? 'text-red-500' : 'text-gray-400'">${{ plan.precio.toLocaleString() }}</span>
              </label>
              <label class="flex flex-col items-center p-3 rounded-xl border-2 cursor-pointer transition-all col-span-2"
                :class="planSeleccionado === 'personalizado' ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'">
                <input type="radio" v-model="planSeleccionado" value="personalizado" class="sr-only">
                <span class="text-xs font-semibold" :class="planSeleccionado === 'personalizado' ? 'text-red-700' : 'text-gray-600'">Personalizado (días)</span>
              </label>
            </div>

            <div v-if="planSeleccionado === 'personalizado'" class="mt-3 grid grid-cols-2 gap-3">
              <div>
                <label class="block text-gray-600 text-xs font-semibold mb-1">Días de acceso</label>
                <input v-model.number="planPersonalizado.dias" type="number" min="1" max="365" class="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-sm" placeholder="Ej. 7" required>
              </div>
              <div>
                <label class="block text-gray-600 text-xs font-semibold mb-1">Monto ($)</label>
                <input v-model.number="planPersonalizado.monto" type="number" min="0" step="any" class="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-sm" placeholder="Ej. 30000" required>
              </div>
            </div>
            <div v-if="planSeleccionado !== 'ninguno' && planSeleccionado !== 'personalizado'" class="mt-3">
              <label class="block text-gray-600 text-xs font-semibold mb-1">Monto cobrado ($)</label>
              <input v-model.number="montoPlanDefault" type="number" min="0" step="1000"
                class="w-full px-3 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-red-500 outline-none text-sm"
                :placeholder="'Sugerido: $' + (planes.find(p => p.id === planSeleccionado)?.precio?.toLocaleString() || '')">
            </div>
          </div>

          <div class="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button @click="cerrarFormulario" type="button" class="px-5 py-2.5 rounded-lg text-gray-600 font-semibold hover:bg-gray-100 transition-colors">Cancelar</button>
            <button type="submit" :disabled="saving" class="px-5 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold shadow-md inline-flex items-center gap-2 transition-all active:scale-95">
              <span v-if="saving" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              {{ saving ? 'Guardando...' : 'Crear Usuario' }}
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

// ── Estado ──────────────────────────────────────────────────
const usuarios = ref([])
const planes = ref([])
const loading = ref(true)
const usuarioSeleccionado = ref(null)
const filtroActivo = ref('todos')

// ── Filtros ──────────────────────────────────────────────────
const hoy = () => { const d = new Date(); d.setHours(0,0,0,0); return d }

const tieneMembresia = (u) => {
  if (!u.fecha_vencimiento) return false
  return new Date(u.fecha_vencimiento + 'T00:00:00') >= hoy()
}

const usuariosFiltrados = computed(() => {
  if (filtroActivo.value === 'activos')    return usuarios.value.filter(u => u.esta_en_gym)
  if (filtroActivo.value === 'membresia') return usuarios.value.filter(tieneMembresia)
  return usuarios.value
})

const tabs = computed(() => [
  { key: 'todos',     label: 'Todos',              count: usuarios.value.length,                          emptyMsg: 'No hay usuarios registrados.' },
  { key: 'membresia', label: 'Con membresía',       count: usuarios.value.filter(tieneMembresia).length,  emptyMsg: 'Ningún usuario tiene membresía activa.' },
  { key: 'activos',   label: 'En el box ahora',     count: usuarios.value.filter(u => u.esta_en_gym).length, emptyMsg: 'No hay usuarios en el box en este momento.' },
])

// ── Crear ────────────────────────────────────────────────────
const showForm = ref(false)
const saving = ref(false)
const nuevoUsuario = ref({ nombre: '', email: '', password: '', rol: 'cliente', telefono: '' })
const planSeleccionado = ref('ninguno')
const montoPlanDefault = ref('')
const planPersonalizado = ref({ dias: '', monto: '' })
const fotoArchivo = ref(null)
const fotoPreview = ref(null)

// ── Editar ───────────────────────────────────────────────────
const showEditar = ref(false)
const guardandoEdicion = ref(false)
const editando = ref(null)
const editForm = ref({ email: '', password: '', telefono: '' })
const editFotoArchivo = ref(null)
const editFotoPreview = ref(null)

// ── Renovar ──────────────────────────────────────────────────
const showRenovar = ref(false)
const guardandoRenovar = ref(false)
const renovarUsuario = ref(null)
const renovarPlan = ref(null)
const renovarDias = ref('')
const renovarMonto = ref('')
const renovarMetodo = ref('efectivo')
const errorRenovar = ref('')

const metodos = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
]

const planSeleccionadoObj = computed(() =>
  renovarPlan.value && renovarPlan.value !== 'personalizado'
    ? planes.value.find(p => p.id === renovarPlan.value) || null
    : null
)

// ── Helpers ──────────────────────────────────────────────────
const fotoSrc = (user, size = 40) =>
  user.foto_url
    ? `http://127.0.0.1:8000${user.foto_url}`
    : `https://ui-avatars.com/api/?name=${encodeURIComponent(user.nombre)}&background=random&size=${size}`

const formatFecha = (f) =>
  new Date(f + 'T12:00:00').toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' })

const formatFechaCorta = (f) =>
  new Date(f).toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' })

const diasRestantes = (fecha) => {
  const hoy = new Date()
  hoy.setHours(0, 0, 0, 0)
  const vence = new Date(fecha + 'T00:00:00')
  return Math.ceil((vence - hoy) / (1000 * 60 * 60 * 24))
}

const etiquetaDias = (dias) => {
  if (dias > 1) return `${dias} días restantes`
  if (dias === 1) return 'Vence mañana'
  if (dias === 0) return 'Vence hoy'
  return `Vencida hace ${Math.abs(dias)} día${Math.abs(dias) !== 1 ? 's' : ''}`
}

const colorTextoDias = (dias) => {
  if (dias > 7) return 'text-emerald-600'
  if (dias > 0) return 'text-amber-600'
  return 'text-red-600'
}

const colorPuntoDias = (dias) => {
  if (dias > 7) return 'bg-emerald-500'
  if (dias > 0) return 'bg-amber-500'
  return 'bg-red-500'
}

const bgCirculoDias = (dias) => {
  if (dias > 7) return 'bg-emerald-100'
  if (dias > 0) return 'bg-amber-100'
  return 'bg-red-100'
}

// ── Fetch ────────────────────────────────────────────────────
const fetchUsuarios = async () => {
  loading.value = true
  try { usuarios.value = (await api.get('/usuarios/')).data }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchPlanes = async () => {
  try { planes.value = (await api.get('/planes/')).data }
  catch (e) { console.error(e) }
}

// ── Ver ──────────────────────────────────────────────────────
const verUsuario = (u) => { usuarioSeleccionado.value = u }

// ── Renovar ──────────────────────────────────────────────────
const abrirRenovar = (user) => {
  renovarUsuario.value = user
  renovarPlan.value = null
  renovarDias.value = ''
  renovarMonto.value = ''
  renovarMetodo.value = 'efectivo'
  errorRenovar.value = ''
  showRenovar.value = true
}

const confirmarRenovacion = async () => {
  if (!renovarPlan.value) return
  guardandoRenovar.value = true
  errorRenovar.value = ''
  try {
    const id = renovarUsuario.value.id
    if (renovarPlan.value === 'personalizado') {
      if (!renovarDias.value || renovarDias.value < 1) {
        errorRenovar.value = 'Ingresa un número de días válido.'
        return
      }
      await api.post('/pagos/directo/', {
        usuario_id: id,
        duracion_dias: renovarDias.value,
        monto: renovarMonto.value || 0,
        metodo_pago: renovarMetodo.value,
      })
    } else {
      const plan = planes.value.find(p => p.id === renovarPlan.value)
      await api.post('/pagos/', {
        usuario_id: id,
        plan_id: renovarPlan.value,
        monto: renovarMonto.value || plan?.precio || 0,
        metodo_pago: renovarMetodo.value,
      })
    }
    showRenovar.value = false
    await fetchUsuarios()
  } catch (e) {
    errorRenovar.value = e.response?.data?.detail || 'Error al renovar la membresía.'
  } finally {
    guardandoRenovar.value = false
  }
}

// ── Crear ────────────────────────────────────────────────────
const cerrarFormulario = () => {
  showForm.value = false
  nuevoUsuario.value = { nombre: '', email: '', password: '', rol: 'cliente', telefono: '' }
  planSeleccionado.value = 'ninguno'
  montoPlanDefault.value = ''
  planPersonalizado.value = { dias: '', monto: '' }
  fotoArchivo.value = null
  fotoPreview.value = null
}

const onFotoChange = (e) => {
  const f = e.target.files[0]
  if (!f) return
  fotoArchivo.value = f
  fotoPreview.value = URL.createObjectURL(f)
}

const quitarFoto = () => { fotoArchivo.value = null; fotoPreview.value = null }

const crearUsuario = async () => {
  saving.value = true
  try {
    const { data: nuevo } = await api.post('/usuarios/', nuevoUsuario.value)

    if (fotoArchivo.value) {
      const fd = new FormData()
      fd.append('foto', fotoArchivo.value)
      await api.post(`/usuarios/${nuevo.id}/foto`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    }

    if (planSeleccionado.value === 'personalizado') {
      await api.post('/pagos/directo/', { usuario_id: nuevo.id, duracion_dias: planPersonalizado.value.dias, monto: planPersonalizado.value.monto })
    } else if (planSeleccionado.value !== 'ninguno') {
      const plan = planes.value.find(p => p.id === planSeleccionado.value)
      await api.post('/pagos/', { usuario_id: nuevo.id, plan_id: planSeleccionado.value, monto: montoPlanDefault.value || plan?.precio || 0 })
    }

    cerrarFormulario()
    await fetchUsuarios()
  } catch (e) {
    const d = e.response?.data?.detail
    alert('Error: ' + (Array.isArray(d) ? d[0].msg : (d || e.message)))
  } finally {
    saving.value = false
  }
}

// ── Editar ───────────────────────────────────────────────────
const confirmarEliminar = async (user) => {
  if (!confirm(`¿Eliminar a ${user.nombre}? Esta acción no se puede deshacer.`)) return
  try {
    await api.delete(`/usuarios/${user.id}`)
    usuarioSeleccionado.value = null
    await fetchUsuarios()
  } catch (e) {
    const d = e.response?.data?.detail
    alert('Error: ' + (Array.isArray(d) ? d[0].msg : (d || e.message)))
  }
}

const abrirEditar = (user) => {
  editando.value = user
  editForm.value = { email: user.email, password: '', telefono: user.telefono || '' }
  editFotoArchivo.value = null
  editFotoPreview.value = null
  showEditar.value = true
}

const cerrarEditar = () => {
  showEditar.value = false
  editando.value = null
  editFotoArchivo.value = null
  editFotoPreview.value = null
}

const onFotoEditChange = (e) => {
  const f = e.target.files[0]
  if (!f) return
  editFotoArchivo.value = f
  editFotoPreview.value = URL.createObjectURL(f)
}

const guardarEdicion = async () => {
  guardandoEdicion.value = true
  try {
    const id = editando.value.id
    const payload = { email: editForm.value.email, telefono: editForm.value.telefono || null }
    if (editForm.value.password) payload.password = editForm.value.password
    await api.patch(`/usuarios/${id}`, payload)

    if (editFotoArchivo.value) {
      const fd = new FormData()
      fd.append('foto', editFotoArchivo.value)
      await api.post(`/usuarios/${id}/foto`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    }

    cerrarEditar()
    await fetchUsuarios()
  } catch (e) {
    const d = e.response?.data?.detail
    alert('Error: ' + (Array.isArray(d) ? d[0].msg : (d || e.message)))
  } finally {
    guardandoEdicion.value = false
  }
}

onMounted(() => { fetchUsuarios(); fetchPlanes() })
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
