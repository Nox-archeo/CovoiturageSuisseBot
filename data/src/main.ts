import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import LocationSearch from '@/components/LocationSearch.vue';

const app = createApp(App);
app.component('LocationSearch', LocationSearch);
app.use(router);
app.mount('#app');
