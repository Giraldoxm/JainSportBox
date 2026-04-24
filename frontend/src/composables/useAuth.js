import { computed } from 'vue'

export function useAuth() {
  const rol = computed(() => localStorage.getItem('userRol') || 'cliente')
  const nombre = computed(() => localStorage.getItem('userName') || '')

  const isAdmin = computed(() => rol.value === 'admin')
  const isCoach = computed(() => rol.value === 'coach')
  const isCliente = computed(() => rol.value === 'cliente')
  const isPendiente = computed(() => rol.value === 'pendiente')
  const canManage = computed(() => rol.value === 'admin' || rol.value === 'coach')

  return { rol, nombre, isAdmin, isCoach, isCliente, isPendiente, canManage }
}
