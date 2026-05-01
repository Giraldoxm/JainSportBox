<template>
  <div>
    <!-- Back -->
    <button @click="$router.back()" class="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-gray-800 mb-6 transition-colors">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/>
      </svg>
      Volver a Usuarios
    </button>

    <!-- Loading -->
    <div v-if="cargando" class="flex justify-center py-24">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-red-600"></div>
    </div>

    <template v-else-if="usuario">

      <!-- ── Perfil ── -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden mb-6">
        <!-- Header rojo -->
        <div class="bg-gradient-to-r from-red-600 to-red-700 px-6 pt-8 pb-6 flex flex-col items-center text-center">
          <img
            class="h-24 w-24 rounded-full object-cover border-4 border-white shadow-lg mb-4"
            :src="fotoSrc(usuario)"
            alt=""
          />
          <h2 class="text-2xl font-black text-white leading-tight">{{ usuario.nombre }}</h2>
          <div class="flex items-center gap-2 mt-2 flex-wrap justify-center">
            <span class="text-xs font-bold px-3 py-1 rounded-full bg-white/20 text-white">
              {{ rolLabel(usuario.rol) }}
            </span>
            <span class="flex items-center gap-1.5 text-xs font-semibold text-white/80">
              <span class="w-2 h-2 rounded-full" :class="usuario.esta_en_gym ? 'bg-green-400' : 'bg-white/40'"></span>
              {{ usuario.esta_en_gym ? 'En el Box' : 'Fuera' }}
            </span>
          </div>
          <button
            @click="abrirEditar"
            class="mt-4 flex items-center gap-1.5 px-4 py-2 rounded-lg bg-white/20 hover:bg-white/30 text-white text-xs font-bold transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
            Editar perfil
          </button>
        </div>

        <!-- Info grid -->
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 p-5">
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Email</p>
            <p class="text-sm font-semibold text-gray-800 break-all">{{ usuario.email }}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Documento</p>
            <p class="text-sm font-semibold text-gray-800">{{ usuario.documento_identidad || '—' }}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Teléfono</p>
            <p class="text-sm font-semibold text-gray-800">{{ usuario.telefono || '—' }}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Género</p>
            <span
              v-if="usuario.genero"
              class="inline-block text-xs font-bold px-2.5 py-1 rounded-full"
              :class="usuario.genero === 'masculino' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'"
            >
              {{ usuario.genero === 'masculino' ? 'Masculino' : 'Femenino' }}
            </span>
            <p v-else class="text-sm text-gray-400">—</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3">
            <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Miembro desde</p>
            <p class="text-sm font-semibold text-gray-800">{{ formatFechaCorta(usuario.created_at) }}</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3 flex items-center justify-between gap-2">
            <div>
              <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Huella digital</p>
              <p class="text-sm font-semibold" :class="usuario.huella_id ? 'text-emerald-700' : 'text-gray-400'">
                {{ usuario.huella_id ? 'Registrada' : 'No registrada' }}
              </p>
            </div>
            <button @click="abrirEnrolamiento" class="flex-shrink-0 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-colors">
              {{ usuario.huella_id ? 'Reemplazar' : 'Registrar' }}
            </button>
          </div>
          <!-- Membresía -->
          <div class="bg-gray-50 rounded-xl p-3 col-span-2 sm:col-span-3">
            <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-2">Membresía</p>
            <template v-if="usuario.fecha_vencimiento">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-bold" :class="colorTextoDias(diasRestantes(usuario.fecha_vencimiento))">
                    {{ etiquetaDias(diasRestantes(usuario.fecha_vencimiento)) }}
                  </p>
                  <p class="text-xs text-gray-500 mt-0.5">Vence el {{ formatFecha(usuario.fecha_vencimiento) }}</p>
                </div>
                <div class="w-12 h-12 rounded-full flex items-center justify-center" :class="bgCirculoDias(diasRestantes(usuario.fecha_vencimiento))">
                  <span class="text-xs font-black" :class="colorTextoDias(diasRestantes(usuario.fecha_vencimiento))">
                    {{ Math.abs(diasRestantes(usuario.fecha_vencimiento)) }}d
                  </span>
                </div>
              </div>
            </template>
            <p v-else class="text-sm text-gray-400">Sin membresía activa</p>
          </div>
        </div>
      </div>

      <!-- ── Asistencias ── -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-xl font-black text-gray-800">Asistencias</h3>
            <p class="text-sm text-gray-500 mt-0.5">Último año</p>
          </div>
          <div v-if="!cargandoAsistencias" class="text-right">
            <p class="text-3xl font-black text-gray-800">{{ totalAsistencias }}</p>
            <p class="text-xs text-gray-400 font-semibold uppercase tracking-wide">días en el año</p>
          </div>
        </div>

        <div v-if="cargandoAsistencias" class="flex justify-center py-10">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
        </div>

        <div v-else class="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm max-w-xs mx-auto">
          <div class="flex items-center justify-between mb-4">
            <button @click="mesOffset--" :disabled="mesOffset <= MIN_OFFSET"
              class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/>
              </svg>
            </button>
            <div class="text-center">
              <p class="text-base font-black text-gray-800">{{ calendarioActual.nombre }}</p>
              <p class="text-xs text-gray-400 font-semibold mt-0.5">
                {{ calendarioActual.count }} día{{ calendarioActual.count !== 1 ? 's' : '' }} asistido{{ calendarioActual.count !== 1 ? 's' : '' }}
              </p>
            </div>
            <button @click="mesOffset++" :disabled="mesOffset >= 0"
              class="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/>
              </svg>
            </button>
          </div>
          <div class="grid grid-cols-7 mb-1">
            <div v-for="d in ['D','L','M','X','J','V','S']" :key="d"
              class="text-center text-xs font-bold text-gray-400 py-0.5">{{ d }}</div>
          </div>
          <div class="grid grid-cols-7 gap-1">
            <template v-for="(cell, idx) in calendarioActual.cells" :key="idx">
              <div v-if="cell === null" />
              <div v-else class="aspect-square rounded-md flex items-center justify-center text-xs font-semibold transition-colors"
                :class="claseCelda(cell)" :title="cell.date">{{ cell.day }}</div>
            </template>
          </div>
        </div>
      </div>

      <!-- ── Historial de suscripciones ── -->
      <div>
        <h3 class="text-xl font-black text-gray-800 mb-4">Historial de Suscripciones</h3>

        <div v-if="cargandoPagos" class="flex justify-center py-10">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
        </div>

        <div v-else-if="pagos.length === 0" class="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-8 text-center">
          <p class="text-gray-400 font-medium">Sin suscripciones registradas</p>
        </div>

        <div v-else class="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100">
                <th class="text-left px-5 py-3 text-xs font-bold text-gray-400 uppercase tracking-wide">Fecha</th>
                <th class="text-left px-5 py-3 text-xs font-bold text-gray-400 uppercase tracking-wide">Plan</th>
                <th class="text-right px-5 py-3 text-xs font-bold text-gray-400 uppercase tracking-wide">Monto</th>
                <th class="text-left px-5 py-3 text-xs font-bold text-gray-400 uppercase tracking-wide hidden sm:table-cell">Método</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in pagos" :key="p.id" class="border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors">
                <td class="px-5 py-3.5 text-gray-600">{{ formatFechaCorta(p.fecha_pago) }}</td>
                <td class="px-5 py-3.5 font-semibold text-gray-800">{{ p.plan_nombre }}</td>
                <td class="px-5 py-3.5 text-right font-bold text-gray-800">${{ p.monto.toLocaleString('es-CO') }}</td>
                <td class="px-5 py-3.5 hidden sm:table-cell">
                  <span class="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold"
                    :class="p.metodo_pago === 'efectivo' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'">
                    {{ p.metodo_pago === 'efectivo' ? 'Efectivo' : 'Transferencia' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>

    <!-- ── Modal: Editar perfil ── -->
    <div v-if="showEditar" class="fixed inset-0 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm z-50 p-4">
      <div class="bg-white rounded-2xl w-full max-w-md shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <!-- Header -->
        <div class="bg-gradient-to-r from-gray-800 to-black px-6 py-5 flex items-center gap-3 flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
          </svg>
          <div>
            <h3 class="text-base font-bold text-white">Editar perfil</h3>
            <p class="text-gray-400 text-xs">{{ usuario?.nombre }}</p>
          </div>
          <button @click="showEditar = false" class="ml-auto text-gray-400 hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <!-- Form -->
        <div class="px-6 py-5 overflow-y-auto flex-1 space-y-4">

          <!-- Nombre -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1.5">Nombre completo</label>
            <input v-model="form.nombre" type="text" placeholder="Nombre completo"
              class="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent transition"/>
          </div>

          <!-- Email -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1.5">Email</label>
            <input v-model="form.email" type="email" placeholder="correo@ejemplo.com"
              class="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent transition"/>
          </div>

          <!-- Teléfono -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1.5">Teléfono</label>
            <input v-model="form.telefono" type="tel" placeholder="Número de teléfono"
              class="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent transition"/>
          </div>

          <!-- Documento -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1.5">Documento de identidad</label>
            <input v-model="form.documento_identidad" type="text" placeholder="Número de documento"
              class="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent transition"/>
          </div>

          <!-- Género -->
          <div>
            <label class="block text-xs font-bold text-gray-500 uppercase tracking-wide mb-1.5">Género</label>
            <div class="grid grid-cols-2 gap-2">
              <button type="button" @click="form.genero = 'masculino'"
                class="py-2.5 rounded-xl border text-sm font-semibold transition-colors"
                :class="form.genero === 'masculino' ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-500 hover:border-gray-300'">
                Masculino
              </button>
              <button type="button" @click="form.genero = 'femenino'"
                class="py-2.5 rounded-xl border text-sm font-semibold transition-colors"
                :class="form.genero === 'femenino' ? 'border-purple-500 bg-purple-50 text-purple-700' : 'border-gray-200 text-gray-500 hover:border-gray-300'">
                Femenino
              </button>
            </div>
          </div>

          <!-- Contraseña -->
          <div class="border-t border-gray-100 pt-4">
            <label class="flex items-center gap-2.5 cursor-pointer mb-3">
              <input type="checkbox" v-model="cambiarPassword" class="w-4 h-4 accent-gray-800 rounded"/>
              <span class="text-sm font-semibold text-gray-700">Cambiar contraseña</span>
            </label>
            <div v-if="cambiarPassword" class="space-y-3">
              <div class="relative">
                <input
                  v-model="form.password"
                  :type="verPassword ? 'text' : 'password'"
                  placeholder="Nueva contraseña (mínimo 6 caracteres)"
                  class="w-full px-3.5 py-2.5 pr-10 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent transition"
                />
                <button type="button" @click="verPassword = !verPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <svg v-if="verPassword" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                  </svg>
                </button>
              </div>
              <p v-if="form.password && form.password.length < 6" class="text-xs text-red-500 font-semibold">
                Mínimo 6 caracteres
              </p>
            </div>
          </div>

          <!-- Error -->
          <p v-if="errorEditar" class="text-xs text-red-600 font-semibold bg-red-50 rounded-lg px-3 py-2">{{ errorEditar }}</p>
        </div>

        <!-- Botones -->
        <div class="px-6 pb-6 flex gap-3 flex-shrink-0">
          <button @click="showEditar = false"
            class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors text-sm">
            Cancelar
          </button>
          <button @click="guardarEdicion" :disabled="guardando"
            class="flex-1 py-2.5 rounded-xl bg-gray-800 hover:bg-black text-white font-bold transition-colors text-sm disabled:bg-gray-300 flex items-center justify-center gap-2">
            <svg v-if="guardando" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
            </svg>
            {{ guardando ? 'Guardando…' : 'Guardar cambios' }}
          </button>
        </div>
      </div>
    </div>

  </div>

  <!-- ── Modal: Enrolamiento de Huella ── -->
  <div v-if="showEnrolModal" class="fixed inset-0 flex items-center justify-center bg-gray-900/70 backdrop-blur-sm z-50 p-4">
    <div class="bg-white rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden">
      <div class="bg-gradient-to-r from-indigo-600 to-indigo-700 px-6 py-5 flex items-center gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M6.625 2.655A9 9 0 0119 11a1 1 0 11-2 0 7 7 0 00-9.625-6.492 1 1 0 11-.75-1.853zM4.662 4.959A1 1 0 014.75 6.37 6.97 6.97 0 003 11a1 1 0 11-2 0 8.97 8.97 0 012.25-5.953 1 1 0 011.412-.088z" clip-rule="evenodd"/>
          <path fill-rule="evenodd" d="M5 11a5 5 0 1110 0 1 1 0 11-2 0 3 3 0 10-6 0c0 1.677-.345 3.276-.968 4.729a1 1 0 11-1.838-.789A9.964 9.964 0 005 11z" clip-rule="evenodd"/>
        </svg>
        <div>
          <h3 class="text-lg font-bold text-white">Registrar Huella</h3>
          <p class="text-indigo-200 text-sm">{{ usuario?.nombre }}</p>
        </div>
        <button v-if="!enrolStatus?.activo" @click="cerrarEnrolModal" class="ml-auto text-white/70 hover:text-white">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>

      <div class="px-6 py-6 text-center">
        <!-- Completado -->
        <div v-if="enrolStatus?.completado" class="flex flex-col items-center gap-3">
          <div class="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
          </div>
          <p class="text-emerald-700 font-bold text-lg">Huella registrada</p>
          <p class="text-gray-500 text-sm">{{ enrolStatus.mensaje }}</p>
          <button @click="cerrarEnrolModal" class="mt-2 w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold transition-colors">Cerrar</button>
        </div>

        <!-- Error -->
        <div v-else-if="enrolStatus?.error" class="flex flex-col items-center gap-3">
          <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </div>
          <p class="text-red-600 font-bold">Error en el enrolamiento</p>
          <p class="text-gray-500 text-sm">{{ enrolStatus.mensaje }}</p>
          <div class="flex gap-3 w-full mt-2">
            <button @click="cerrarEnrolModal" class="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-semibold hover:bg-gray-50 transition-colors">Cancelar</button>
            <button @click="iniciarEnrolamiento" class="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold transition-colors">Reintentar</button>
          </div>
        </div>

        <!-- En progreso -->
        <div v-else-if="enrolStatus?.activo" class="flex flex-col items-center gap-4">
          <div class="relative w-20 h-20">
            <div class="absolute inset-0 rounded-full bg-indigo-100 animate-ping opacity-40"></div>
            <div class="relative w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center border-2 border-indigo-300">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-indigo-600" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M6.625 2.655A9 9 0 0119 11a1 1 0 11-2 0 7 7 0 00-9.625-6.492 1 1 0 11-.75-1.853zM4.662 4.959A1 1 0 014.75 6.37 6.97 6.97 0 003 11a1 1 0 11-2 0 8.97 8.97 0 012.25-5.953 1 1 0 011.412-.088z" clip-rule="evenodd"/>
                <path fill-rule="evenodd" d="M5 11a5 5 0 1110 0 1 1 0 11-2 0 3 3 0 10-6 0c0 1.677-.345 3.276-.968 4.729a1 1 0 11-1.838-.789A9.964 9.964 0 005 11z" clip-rule="evenodd"/>
              </svg>
            </div>
          </div>
          <div class="flex gap-2">
            <div v-for="i in enrolStatus.total" :key="i"
              class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all"
              :class="i < enrolStatus.paso ? 'bg-emerald-500 text-white' :
                      i === enrolStatus.paso ? 'bg-indigo-600 text-white ring-4 ring-indigo-200' :
                      'bg-gray-100 text-gray-400'">
              {{ i < enrolStatus.paso ? '✓' : i }}
            </div>
          </div>
          <p class="text-gray-700 font-semibold">{{ enrolStatus.mensaje }}</p>
          <p class="text-gray-400 text-sm">Captura {{ enrolStatus.paso }} de {{ enrolStatus.total }}</p>
          <button @click="cancelarEnrolamiento" class="mt-1 text-sm text-red-500 hover:text-red-700 font-medium">Cancelar</button>
        </div>

        <!-- Inicio / bridge desconectado -->
        <div v-else class="flex flex-col items-center gap-4">
          <div v-if="enrolBridgeError" class="w-full p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-700 text-sm">
            <p class="font-semibold">Bridge no disponible</p>
            <p class="mt-1">Asegúrate de que el bridge esté corriendo:<br>
              <code class="text-xs bg-amber-100 px-1 rounded">dotnet run --project servicio_biometrico/HuelleroBridge.csproj</code>
            </p>
          </div>
          <div v-else>
            <p class="text-gray-500 text-sm mb-4">Se capturarán <strong>4 muestras</strong> del dedo del usuario.<br>Asegúrate de que el lector esté conectado.</p>
            <button @click="iniciarEnrolamiento" class="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-lg transition-colors flex items-center justify-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clip-rule="evenodd"/>
              </svg>
              Iniciar captura
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'

const route = useRoute()
const id = route.params.id

const usuario = ref(null)
const cargando = ref(true)
const fechasAsistencia = ref([])
const cargandoAsistencias = ref(true)
const pagos = ref([])
const cargandoPagos = ref(true)

// ── Editar ──────────────────────────────────────────────────
const showEditar = ref(false)
const guardando = ref(false)
const errorEditar = ref('')
const cambiarPassword = ref(false)
const verPassword = ref(false)
const form = ref({})

function abrirEditar() {
  form.value = {
    nombre: usuario.value.nombre,
    email: usuario.value.email,
    telefono: usuario.value.telefono || '',
    documento_identidad: usuario.value.documento_identidad || '',
    genero: usuario.value.genero || '',
    password: '',
  }
  cambiarPassword.value = false
  verPassword.value = false
  errorEditar.value = ''
  showEditar.value = true
}

async function guardarEdicion() {
  errorEditar.value = ''

  if (cambiarPassword.value && form.value.password.length < 6) {
    errorEditar.value = 'La contraseña debe tener al menos 6 caracteres.'
    return
  }

  const payload = {}
  if (form.value.nombre !== usuario.value.nombre) payload.nombre = form.value.nombre
  if (form.value.email !== usuario.value.email) payload.email = form.value.email
  if (form.value.telefono !== (usuario.value.telefono || '')) payload.telefono = form.value.telefono
  if (form.value.documento_identidad !== (usuario.value.documento_identidad || '')) payload.documento_identidad = form.value.documento_identidad
  if (form.value.genero !== (usuario.value.genero || '')) payload.genero = form.value.genero
  if (cambiarPassword.value && form.value.password) payload.password = form.value.password

  if (Object.keys(payload).length === 0) {
    showEditar.value = false
    return
  }

  guardando.value = true
  try {
    const { data } = await api.patch(`/usuarios/${id}`, payload)
    usuario.value = data
    showEditar.value = false
  } catch (e) {
    errorEditar.value = e.response?.data?.detail || 'Error al guardar los cambios.'
  } finally {
    guardando.value = false
  }
}

// ── Enrolamiento de huella ────────────────────────────────────
const BRIDGE_URL = 'http://localhost:8001'
const showEnrolModal = ref(false)
const enrolStatus = ref(null)
const enrolBridgeError = ref(false)
let enrolPollInterval = null

const abrirEnrolamiento = () => {
  enrolStatus.value = null
  enrolBridgeError.value = false
  showEnrolModal.value = true
}

const cerrarEnrolModal = () => {
  clearInterval(enrolPollInterval)
  enrolPollInterval = null
  showEnrolModal.value = false
  enrolStatus.value = null
  // Refrescar el usuario para reflejar huella_id actualizado
  api.get(`/usuarios/${id}`).then(r => { usuario.value = r.data }).catch(() => {})
}

const iniciarEnrolamiento = async () => {
  enrolBridgeError.value = false
  try {
    const nombre = encodeURIComponent(usuario.value.nombre)
    await fetch(`${BRIDGE_URL}/enroll/${id}?nombre=${nombre}`, { method: 'POST' })
    enrolStatus.value = { activo: true, completado: false, error: false, paso: 0, total: 4, mensaje: 'Coloca el dedo en el lector' }
    _iniciarPollEnrol()
  } catch {
    enrolBridgeError.value = true
  }
}

const cancelarEnrolamiento = async () => {
  try { await fetch(`${BRIDGE_URL}/enroll`, { method: 'DELETE' }) } catch {}
  clearInterval(enrolPollInterval)
  enrolPollInterval = null
  enrolStatus.value = null
}

const _pollStatus = async () => {
  try {
    const r = await fetch(`${BRIDGE_URL}/status`)
    const data = await r.json()
    enrolStatus.value = data.enrolamiento
    if (data.enrolamiento.completado || (data.enrolamiento.error && !data.enrolamiento.activo)) {
      clearInterval(enrolPollInterval)
      enrolPollInterval = null
    }
  } catch {
    enrolBridgeError.value = true
    clearInterval(enrolPollInterval)
    enrolPollInterval = null
  }
}

const _iniciarPollEnrol = () => {
  clearInterval(enrolPollInterval)
  _pollStatus()
  enrolPollInterval = setInterval(_pollStatus, 600)
}

// ── Helpers de perfil ───────────────────────────────────────
const BASE_URL = 'http://127.0.0.1:8000'
const fotoSrc = (u) => u?.foto_url
  ? `${BASE_URL}${u.foto_url}`
  : `https://ui-avatars.com/api/?name=${encodeURIComponent(u?.nombre || 'U')}&background=dc2626&color=fff&size=128`

const rolLabel = (rol) => ({ admin: 'Administrador', coach: 'Coach', cliente: 'Cliente', pendiente: 'Pendiente' }[rol] || rol)

function formatFecha(f) {
  if (!f) return ''
  return new Date(f + 'T12:00:00').toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })
}

function formatFechaCorta(f) {
  if (!f) return ''
  return new Date(f).toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })
}

function diasRestantes(fecha) {
  const hoy = new Date(); hoy.setHours(0, 0, 0, 0)
  const vence = new Date(fecha + 'T00:00:00')
  return Math.ceil((vence - hoy) / 86400000)
}

function colorTextoDias(d) {
  if (d < 0) return 'text-red-600'
  if (d <= 7) return 'text-amber-600'
  return 'text-emerald-600'
}

function bgCirculoDias(d) {
  if (d < 0) return 'bg-red-100'
  if (d <= 7) return 'bg-amber-100'
  return 'bg-emerald-100'
}

function etiquetaDias(d) {
  if (d < 0) return `Venció hace ${Math.abs(d)} día${Math.abs(d) !== 1 ? 's' : ''}`
  if (d === 0) return 'Vence hoy'
  if (d === 1) return 'Vence mañana'
  return `${d} días restantes`
}

// ── Calendario ──────────────────────────────────────────────
const MIN_OFFSET = -11
const mesOffset = ref(0)

const attendedSet = computed(() => new Set(fechasAsistencia.value))
const totalAsistencias = computed(() => fechasAsistencia.value.length)

const MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

function buildMonth(year, month) {
  const today = new Date()
  const firstDow = new Date(year, month, 1).getDay()
  const totalDays = new Date(year, month + 1, 0).getDate()
  const cells = []
  for (let i = 0; i < firstDow; i++) cells.push(null)
  for (let d = 1; d <= totalDays; d++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const dayDate = new Date(year, month, d)
    cells.push({
      day: d,
      date: dateStr,
      attended: attendedSet.value.has(dateStr),
      isFuture: dayDate > today,
      isToday: d === today.getDate() && month === today.getMonth() && year === today.getFullYear(),
    })
  }
  return {
    nombre: `${MESES[month]} ${year}`,
    key: `${year}-${month}`,
    count: cells.filter(c => c?.attended).length,
    cells,
  }
}

const calendarioActual = computed(() => {
  const today = new Date()
  let y = today.getFullYear()
  let m = today.getMonth() + mesOffset.value
  while (m < 0) { m += 12; y-- }
  while (m > 11) { m -= 12; y++ }
  return buildMonth(y, m)
})

function claseCelda(cell) {
  if (cell.isFuture) return 'bg-gray-50 text-gray-300 cursor-default'
  if (cell.attended && cell.isToday) return 'bg-emerald-500 text-white ring-2 ring-emerald-300'
  if (cell.attended) return 'bg-emerald-500 text-white'
  if (cell.isToday) return 'bg-gray-800 text-white'
  return 'bg-transparent text-gray-400'
}

// ── Fetch ───────────────────────────────────────────────────
onMounted(async () => {
  const [userRes, asistRes, pagosRes] = await Promise.allSettled([
    api.get(`/usuarios/${id}`),
    api.get(`/asistencia/historial/${id}?meses=12`),
    api.get(`/pagos/usuario/${id}`),
  ])

  if (userRes.status === 'fulfilled') usuario.value = userRes.value.data
  cargando.value = false

  if (asistRes.status === 'fulfilled') fechasAsistencia.value = asistRes.value.data.fechas || []
  cargandoAsistencias.value = false

  if (pagosRes.status === 'fulfilled') pagos.value = pagosRes.value.data || []
  cargandoPagos.value = false
})
</script>
