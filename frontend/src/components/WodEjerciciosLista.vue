<template>
  <div v-if="ejercicios && ejercicios.length > 0" :class="dark ? 'space-y-2' : 'space-y-1.5'">
    <div
      v-for="(ej, idx) in ejercicios"
      :key="ej.ejercicio_id ?? idx"
      class="flex items-start gap-2 rounded-lg px-3 py-2"
      :class="dark ? 'bg-white/10' : 'bg-gray-50 border border-gray-100'"
    >
      <span class="text-xs font-bold flex-shrink-0 mt-0.5" :class="dark ? 'opacity-70' : 'text-gray-400'">{{ idx + 1 }}.</span>
      <div class="flex-1 min-w-0">
        <p class="font-semibold text-sm leading-tight" :class="dark ? 'text-white' : 'text-gray-800'">{{ ej.nombre }}</p>
        <p v-if="ej.notas" class="text-xs mt-0.5 whitespace-pre-line" :class="dark ? 'opacity-90' : 'text-gray-500'">{{ ej.notas }}</p>
      </div>
      <a
        v-if="ej.video_url"
        :href="ej.video_url"
        target="_blank"
        rel="noopener noreferrer"
        class="flex-shrink-0 inline-flex items-center gap-1 text-xs font-semibold rounded-md px-2 py-1 transition-colors"
        :class="dark ? 'bg-white/20 hover:bg-white/30 text-white' : 'bg-red-50 hover:bg-red-100 text-red-600'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
        Video
      </a>
    </div>
  </div>
</template>

<script setup>
defineProps({
  ejercicios: { type: Array, default: () => [] },
  dark: { type: Boolean, default: false },
})
</script>
