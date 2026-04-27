import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import UsuariosView from '../views/UsuariosView.vue'
import PlanesView from '../views/PlanesView.vue'
import TiendaView from '../views/TiendaView.vue'
import LoginView from '../views/LoginView.vue'
import WodsView from '../views/WodsView.vue'
import FinanzasView from '../views/FinanzasView.vue'
import SaludView from '../views/SaludView.vue'
import SaludMedidaView from '../views/SaludMedidaView.vue'
import MarcasView from '../views/MarcasView.vue'
import MarcasEjercicioView from '../views/MarcasEjercicioView.vue'
import AlertasView from '../views/AlertasView.vue'
import WodsPersonalizadosView from '../views/WodsPersonalizadosView.vue'
import HomeView from '../views/HomeView.vue'
import UsuarioPerfilView from '../views/UsuarioPerfilView.vue'

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
        path: '',
        redirect: () => {
          const rol = localStorage.getItem('userRol') || 'cliente'
          if (rol === 'pendiente') return '/planes'
          if (rol === 'admin') return '/usuarios'
          return '/home'
        }
      },
      {
        path: 'usuarios',
        name: 'Usuarios',
        component: UsuariosView,
        meta: { roles: ['admin', 'coach'] }
      },
      {
        path: 'usuarios/:id',
        name: 'UsuarioPerfil',
        component: UsuarioPerfilView,
        meta: { roles: ['admin', 'coach'] }
      },
      {
        path: 'planes',
        name: 'Planes',
        component: PlanesView,
        meta: { roles: ['admin', 'coach', 'cliente', 'pendiente'] }
      },
      {
        path: 'tienda',
        name: 'Tienda',
        component: TiendaView,
        meta: { roles: ['admin', 'coach'] }
      },
      {
        path: 'wods',
        name: 'WODs',
        component: WodsView
      },
      {
        path: 'finanzas',
        name: 'Finanzas',
        component: FinanzasView,
        meta: { roles: ['admin'] }
      },
      {
        path: 'salud',
        name: 'Salud',
        component: SaludView,
      },
      {
        path: 'salud/:tipo',
        name: 'SaludMedida',
        component: SaludMedidaView,
      },
      {
        path: 'marcas',
        name: 'Marcas',
        component: MarcasView,
      },
      {
        path: 'marcas/:ejercicio',
        name: 'MarcasEjercicio',
        component: MarcasEjercicioView,
      },
      {
        path: 'alertas',
        name: 'Alertas',
        component: AlertasView,
        meta: { roles: ['admin', 'coach'] },
      },
      {
        path: 'wods/personalizados',
        name: 'WodsPersonalizados',
        component: WodsPersonalizadosView,
        meta: { roles: ['admin', 'cliente'] },
      },
      {
        path: 'home',
        name: 'Home',
        component: HomeView,
        meta: { roles: ['cliente', 'coach'] },
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const rol = localStorage.getItem('userRol') || 'cliente'

  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  if (to.path === '/login' && token) {
    return next('/')
  }

  // Usuarios pendientes solo pueden ver /planes
  if (rol === 'pendiente' && to.path !== '/planes' && to.path !== '/') {
    return next('/planes')
  }

  if (to.meta.roles && !to.meta.roles.includes(rol)) {
    return next(rol === 'admin' ? '/usuarios' : '/home')
  }

  next()
})

export default router
