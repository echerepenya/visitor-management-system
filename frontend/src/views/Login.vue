<template>
  <div class="min-h-screen bg-yellow-50 flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-white border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-8">
      <header class="text-center mb-8">
        <h1 class="text-3xl font-black uppercase tracking-tighter">VMS GUARD</h1>
        <p class="font-bold text-gray-500 uppercase text-sm">Вхід у систему охорони</p>
      </header>

      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label class="block text-sm font-black uppercase mb-1">Логін</label>
          <input v-model="form.username" type="text" required
                 class="w-full border-2 border-black p-3 font-bold focus:bg-yellow-50 outline-none transition-colors"
                 placeholder="Введіть ваш ID">
        </div>

        <div>
          <label class="block text-sm font-black uppercase mb-1">Пароль</label>
          <input v-model="form.password" type="password" required
                 class="w-full border-2 border-black p-3 font-bold focus:bg-yellow-50 outline-none transition-colors"
                 placeholder="••••••••">
        </div>

        <div v-if="error" class="bg-red-100 border-2 border-red-500 p-3 text-red-600 font-bold text-sm">
          {{ error }}
        </div>

        <button :disabled="loading" type="submit"
                class="w-full bg-black text-black font-black py-4 uppercase hover:bg-gray-800 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.3)] active:translate-y-1 transition-all">
          {{ loading ? 'Завантаження...' : 'Увійти' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '@/store/auth';
import { useRouter } from 'vue-router';

const auth = useAuthStore();
const router = useRouter();

const form = ref({ username: '', password: '' });
const error = ref('');
const loading = ref(false);

const handleLogin = async () => {
  loading.value = true;
  error.ref = '';
  try {
    await auth.login(form.value);
    router.push('/');
  } catch (e) {
    error.value = 'Помилка авторизації. Перевірте дані.';
  } finally {
    loading.value = false;
  }
};
</script>
