import { createRouter, createWebHistory } from 'vue-router';
import CreateTrip from '@/views/CreateTrip.vue';

// ...existing code...

const routes = [
  // ...existing code...
  {
    path: '/creer',
    name: 'CreateTrip',
    component: CreateTrip
  }
];

// ...existing code...

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;