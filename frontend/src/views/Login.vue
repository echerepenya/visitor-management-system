<template>
  <div class="fixed inset-0 h-[100dvh] w-full bg-yellow-50 flex flex-col items-center justify-center p-0 md:p-4 overflow-hidden">

    <div class="w-full h-full md:h-auto md:max-w-md bg-white md:border-4 md:border-black md:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] flex flex-col">

      <header class="pt-12 px-8 pb-6 flex-none text-center bg-yellow-50 md:bg-white border-b-4 border-black md:border-none">
        <h1 class="text-4xl font-black uppercase tracking-tighter">VMS GUARD</h1>
        <p class="font-bold text-gray-500 uppercase text-xs tracking-widest mt-2">Вхід у систему</p>
      </header>

      <form @submit.prevent="handleLogin" class="flex-grow flex flex-col justify-center px-8 bg-white space-y-6">

        <div>
          <label class="block text-sm font-black uppercase mb-2">Логін</label>
          <input v-model="form.username" type="text" required
                 class="w-full border-4 border-black p-4 text-lg font-bold outline-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] focus:translate-x-[2px] focus:translate-y-[2px] focus:shadow-none transition-all rounded-none appearance-none"
                 placeholder="ID">
        </div>

        <div>
          <label class="block text-sm font-black uppercase mb-2">Пароль</label>
          <input v-model="form.password" type="password" required
                 class="w-full border-4 border-black p-4 text-lg font-bold outline-none shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] focus:translate-x-[2px] focus:translate-y-[2px] focus:shadow-none transition-all rounded-none appearance-none"
                 placeholder="••••">
        </div>

        <div v-if="error" class="bg-red-500 text-white p-3 font-bold text-center border-2 border-black">
          {{ error }}
        </div>

      </form>

      <div class="p-8 bg-white flex-none">
        <button :disabled="loading" type="submit"
                class="w-full bg-black text-white font-black py-5 text-xl uppercase shadow-[4px_4px_0px_0px_rgba(0,0,0,0.3)] active:translate-y-1 active:shadow-none transition-all">
          {{ loading ? '...' : 'УВІЙТИ' }}
        </button>
      </div>

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
