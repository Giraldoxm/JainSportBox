<template>
  <!-- Input de contraseña con ojito para mostrarla. Es un componente y no markup
       repetido porque son 7 campos de contraseña en la app, y el SVG del ojo son
       6 líneas cada vez. -->
  <div class="relative">
    <input
      ref="el"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
      :type="visible ? 'text' : 'password'"
      :required="required"
      :minlength="minlength"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :disabled="disabled"
      :class="[inputClass, 'pr-10']"
    />
    <button
      type="button"
      @click="visible = !visible"
      :title="visible ? 'Ocultar contraseña' : 'Mostrar contraseña'"
      :aria-label="visible ? 'Ocultar contraseña' : 'Mostrar contraseña'"
      class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
    >
      <svg v-if="visible" xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  modelValue: { type: String, default: '' },
  // Las clases del input las pone quien lo usa: cada pantalla tiene su estilo de
  // borde y de focus, y el componente no las va a unificar por su cuenta.
  inputClass: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  autocomplete: { type: String, default: 'off' },
  required: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  minlength: { type: [String, Number], default: undefined },
})
defineEmits(['update:modelValue'])

// Arranca oculta siempre: que el estado no sobreviva entre aperturas del modal.
const visible = ref(false)

// Un ref sobre el componente apunta a la instancia, no al <input>, así que hay que
// exponer focus() a mano. Lo usa el modal del kiosco, que enfoca al abrirse.
const el = ref(null)
defineExpose({ focus: () => el.value?.focus() })
</script>
