import 'bootstrap/dist/css/bootstrap.css';
import { createApp } from "vue";
import axios from 'axios';

import App from './App.vue';
import router from './router';
import store from './store';

const app = createApp(App);

// Configure axios defaults with more detailed error logging
axios.defaults.baseURL = 'http://localhost:5000';
axios.defaults.headers.common['Accept'] = 'application/json';
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Add response interceptor for debugging
axios.interceptors.response.use(
  response => {
    console.log('API Response:', response);
    return response;
  },
  error => {
    console.error('API Error:', error.response?.data || error.message);
    console.error('Full error:', error);
    return Promise.reject(error);
  }
);

// Add request interceptor for debugging
axios.interceptors.request.use(
  config => {
    console.log('API Request:', config.method.toUpperCase(), config.url);
    return config;
  },
  error => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

app.use(router);
app.use(store);
app.mount("#app"); 