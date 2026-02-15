import { defineStore } from 'pinia';
import api from '@/api';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
  }),
  actions: {
async login(credentials) {
    const params = new URLSearchParams();

    params.append('username', credentials.username);
    params.append('password', credentials.password);

    const res = await api.post('/auth/login', params);

    this.token = res.data.access_token;
    this.user = res.data.user || null;

    localStorage.setItem('token', this.token);
  },
    logout() {
      this.token = null;
      this.user = null;

      localStorage.removeItem('token');

      window.location.href = '/login';
    }
  }
});
