<template>
  <div class="h-[100dvh] w-full bg-yellow-50 flex items-center justify-center p-2 overflow-hidden fixed inset-0">

    <Transition
      appear
      enter-active-class="transition duration-700 ease-out"
      enter-from-class="opacity-0 scale-95 translate-y-10"
      enter-to-class="opacity-100 scale-100 translate-y-0"
    >
      <div class="w-full max-w-md min-h-[80dvh] md:min-h-0 bg-white border-4 border-black shadow-[10px_10px_0px_0px_rgba(0,0,0,1)] p-8 md:p-10 flex flex-col justify-center">

        <header class="text-center mb-10 md:mb-8">
          <h1 class="text-4xl md:text-5xl font-black uppercase tracking-tighter animate-in fade-in slide-in-from-top duration-700">
            VMS GUARD
          </h1>
          <div class="h-2 w-20 bg-black mx-auto mt-2 mb-4"></div>
          <p class="font-bold text-gray-500 uppercase text-sm tracking-widest delay-100 animate-in fade-in duration-700">
            Вхід у систему охорони
          </p>
        </header>

        <form @submit.prevent="handleLogin" class="space-y-8 md:space-y-6 flex-grow flex flex-col justify-center">
          <div class="delay-200 animate-in fade-in slide-in-from-left duration-500 fill-mode-both">
            <label class="block text-md font-black uppercase mb-2">Логін Користувача</label>
            <input v-model="form.username" type="text" required
                   class="w-full border-4 border-black p-4 font-bold focus:bg-yellow-50 outline-none transition-all focus:translate-x-1 focus:translate-y-1 focus:shadow-none shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] text-lg"
                   placeholder="username">
          </div>

          <div class="delay-300 animate-in fade-in slide-in-from-left duration-500 fill-mode-both">
            <label class="block text-md font-black uppercase mb-2">Пароль доступу</label>
            <input v-model="form.password" type="password" required
                   class="w-full border-4 border-black p-4 font-bold focus:bg-yellow-50 outline-none transition-all focus:translate-x-1 focus:translate-y-1 focus:shadow-none shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] text-lg"
                   placeholder="••••••••">
          </div>

          <Transition
            enter-active-class="transition duration-300 ease-out"
            enter-from-class="opacity-0 -translate-y-2"
            enter-to-class="opacity-100 translate-y-0"
          >
            <div v-if="error" class="bg-red-500 text-white border-4 border-black p-4 font-black text-sm uppercase">
              Помилка: {{ error }}
            </div>
          </Transition>

          <div class="delay-500 animate-in fade-in zoom-in duration-500 fill-mode-both pt-4">
            <button :disabled="loading" type="submit"
                    class="w-full bg-black text-white font-black py-5 text-xl uppercase
                           hover:bg-gray-800 active:translate-x-1 active:translate-y-1
                           active:shadow-none shadow-[6px_6px_0px_0px_rgba(0,0,0,0.3)]
                           transition-all disabled:opacity-50">
              <span v-if="loading" class="flex items-center justify-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Авторизація...
              </span>
              <span v-else>Увійти в систему</span>
            </button>
          </div>
        </form>

        <footer class="mt-8 text-center text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] delay-700 animate-in fade-in">
          Secure Terminal v1.1.0
        </footer>
      </div>
    </Transition>
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
