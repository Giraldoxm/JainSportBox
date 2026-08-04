<script setup>
// Visor de foto a pantalla completa. El padre lo monta con v-if, así el listener de
// Escape y el bloqueo de scroll se instalan y se limpian solos con el ciclo de vida.
import { onMounted, onUnmounted } from 'vue'

defineProps({
  src: { type: String, required: true },
  nombre: { type: String, default: '' },
})

const emit = defineEmits(['cerrar'])

const alPresionarTecla = (e) => {
  if (e.key === 'Escape') emit('cerrar')
}

onMounted(() => {
  window.addEventListener('keydown', alPresionarTecla)
  // Sin esto la página de atrás sigue scrolleando bajo el overlay.
  document.body.style.overflow = 'hidden'
})

onUnmounted(() => {
  window.removeEventListener('keydown', alPresionarTecla)
  document.body.style.overflow = ''
})
</script>

<template>
  <!-- Teleport: si el overlay se quedara dentro de la tarjeta del perfil, heredaría su
       overflow-hidden y su contexto de apilamiento, y saldría recortado. -->
  <Teleport to="body">
    <div class="fixed inset-0 z-[60] bg-gray-950/90 backdrop-blur-sm flex flex-col items-center justify-center p-4 sm:p-8"
      role="dialog" aria-modal="true" :aria-label="`Foto de ${nombre}`" @click="emit('cerrar')">
      <button @click="emit('cerrar')" aria-label="Cerrar"
        class="absolute top-4 right-4 p-2 rounded-full text-white/70 hover:text-white hover:bg-white/10 transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- object-contain y no cover: acá la foto se mira para reconocer a alguien, así
           que no se recorta aunque quede con bandas a los costados. -->
      <img :src="src" :alt="nombre" @click.stop
        class="max-h-[80vh] max-w-full rounded-2xl object-contain shadow-2xl" />

      <p v-if="nombre" class="mt-4 text-white font-semibold text-lg text-center">{{ nombre }}</p>
      <p class="mt-1 text-white/50 text-xs">Clic afuera o Esc para cerrar</p>
    </div>
  </Teleport>
</template>
