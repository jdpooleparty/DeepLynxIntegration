import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/ontology',
    name: 'ontology',
    component: () => import('../views/OntologyView.vue')
  },
  {
    path: '/datasources',
    name: 'datasources',
    component: () => import('../views/DataSourcesView.vue')
  },
  {
    path: '/typemappings',
    name: 'typemappings',
    component: () => import('../views/TypeMappingsView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 