import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import UsuariosView from '../views/UsuariosView.vue'
import TiendaView from '../views/TiendaView.vue'

const routes = [
  {
    path: '/',
    component: Dashboard,
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

export default router
