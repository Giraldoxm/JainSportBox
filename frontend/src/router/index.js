import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import UsuariosView from '../views/UsuariosView.vue'
import TiendaView from '../views/TiendaView.vue'
import LoginView from '../views/LoginView.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView
  },
  {
    path: '/',
    component: Dashboard,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'usuarios',
        name: 'Usuarios',
        component: UsuariosView
      },
      {
        path: 'tienda',
        name: 'Tienda',
        component: TiendaView
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Router Guard: Redirigir a /login si no hay token
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
