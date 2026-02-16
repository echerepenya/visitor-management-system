<template>
  <div class="w-[90%] mx-auto p-4 pb-20">

    <header class="flex justify-between items-center mb-8 border-b-4 border-black pb-4">
      <div>
        <h1 class="text-3xl font-black text-gray-900 uppercase tracking-tighter">ЖУРНАЛ ОХОРОНИ</h1>
        <p class="text-gray-600 font-bold text-sm mt-1">Оновлюється автоматично • {{ currentDate }}</p>
      </div>
      <button @click="auth.logout()"
              class="bg-red-600 text-black font-bold uppercase px-6 py-3 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all">
        Вийти
      </button>
    </header>

    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-4 border-black"></div>
    </div>

    <div v-else class="overflow-hidden border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] bg-white rounded-lg">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-black text-white uppercase text-sm leading-normal">
            <th class="py-4 px-6 font-bold w-32 text-center">Тип</th>
            <th class="py-4 px-6 font-bold w-1/4">Гість / Авто</th>
            <th class="py-4 px-6 font-bold">Коментар</th>
            <th class="py-4 px-6 font-bold w-48 text-right">Час</th>
            <th class="py-4 px-6 font-bold w-24 text-center">Статус</th>
          </tr>
        </thead>
        <tbody class="text-gray-900 text-base font-bold">

          <tr v-for="req in sortedRequests" :key="req.id"
              @click="req.status !== 'closed' && openConfirm(req)"
              class="border-b-4 border-black last:border-b-0 transition-all duration-200"
              :class="req.status === 'closed' ? 'bg-gray-100 text-gray-400 cursor-default' : 'cursor-pointer hover:bg-yellow-50 group'">

            <td class="py-6 px-6 text-center border-r-2 border-gray-100 transition-colors"
                :class="{ 'opacity-50 grayscale': req.status === 'completed' }">
              <span :class="getTypeColor(req.type)"
                    class="py-2 px-3 border-2 border-black text-xs font-black uppercase shadow-[2px_2px_0px_0px_rgba(0,0,0,0.2)] whitespace-nowrap">
                {{ translateType(req.type) }}
              </span>
            </td>

            <td class="py-6 px-6 border-r-2 border-gray-100 transition-colors">
              <div class="text-2xl font-black uppercase tracking-wide"
                   :class="{ 'line-through decoration-4 decoration-black/30': req.status === 'completed' }">
                {{ req.value }}
              </div>
            </td>

            <td class="py-6 px-6 border-r-2 border-gray-100 transition-colors font-medium">
              {{ req.comment || '—' }}
            </td>

            <td class="py-6 px-6 border-r-2 border-gray-100 transition-colors text-right">
              <div class="text-xl font-mono font-bold">{{ formatTime(req.created_at) }}</div>
              <div class="text-xs uppercase font-bold opacity-60">{{ formatDate(req.created_at) }}</div>
            </td>

            <td class="py-6 px-6 text-center">
              <div v-if="req.status !== 'completed'"
                   class="w-10 h-10 bg-black text-white flex items-center justify-center rounded-full group-hover:scale-110 group-hover:bg-green-600 transition-all shadow-[2px_2px_0px_0px_rgba(0,0,0,0.3)]">
                ➝
              </div>

              <div v-else
                   class="w-10 h-10 border-4 border-gray-300 text-gray-300 flex items-center justify-center rounded-full font-black text-xl bg-gray-50">
                ✓
              </div>
            </td>
          </tr>

          <tr v-if="requests.length === 0">
            <td colspan="5" class="py-20 text-center bg-gray-50">
              <p class="text-xl font-black uppercase text-gray-400">Немає заявок</p>
            </td>
          </tr>

        </tbody>
      </table>
    </div>

    <div v-if="selectedRequest" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50" @click.self="selectedRequest = null">
      <div class="bg-white border-4 border-black p-8 max-w-md w-full shadow-[12px_12px_0px_0px_rgba(255,255,255,1)] relative">
        <button @click="selectedRequest = null" class="absolute top-2 right-2 text-2xl font-bold hover:text-red-600 px-2">&times;</button>
        <h2 class="text-2xl font-black mb-6 uppercase border-b-4 border-yellow-300 inline-block">Пропустити?</h2>

        <div class="bg-gray-100 p-4 border-2 border-black mb-6">
          <p class="text-sm text-gray-500 uppercase font-bold mb-1">Гість / Авто:</p>
          <p class="text-4xl font-black mb-4 uppercase">{{ selectedRequest.value }}</p>

          <div v-if="selectedRequest.comment" class="border-t-2 border-gray-300 pt-2 mt-2">
             <p class="text-sm text-gray-500 uppercase font-bold mb-1">Коментар:</p>
             <p class="font-bold text-lg">{{ selectedRequest.comment }}</p>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <button @click="selectedRequest = null" class="border-2 border-black py-4 font-black uppercase hover:bg-gray-200 transition-colors">Скасувати</button>
          <button @click="closeRequest" class="bg-green-600 text-black border-2 border-black py-4 font-black uppercase hover:bg-green-700 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all">Так, пропустив</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useAuthStore } from '@/store/auth';
import api from '@/api';

const auth = useAuthStore();
const requests = ref([]);
const loading = ref(true);
const selectedRequest = ref(null);
const currentDate = ref('');
let interval = null;

const updateDate = () => {
  const date = new Date();
  const options = { weekday: 'long', day: 'numeric', month: 'long' };
  let dateString = date.toLocaleDateString('uk-UA', options);

  currentDate.value = dateString.charAt(0).toUpperCase() + dateString.slice(1);
};

const sortedRequests = computed(() => {
  return [...requests.value].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
});

const fetchRequests = async () => {
  try {
    const res = await api.get('/requests/');
    requests.value = res.data;
  } catch (e) {
    console.error("Помилка API:", e);
  } finally {
    loading.value = false;
  }
};

const openConfirm = (req) => {
  if (req.status !== 'new') return;

  selectedRequest.value = req;
};

const closeRequest = async () => {
  if (!selectedRequest.value) return;
  try {
    await api.post(`/requests/${selectedRequest.value.id}/complete`);

    const req = requests.value.find(r => r.id === selectedRequest.value.id);
    if (req) req.status = 'completed';
    selectedRequest.value = null;
  } catch (e) {
    alert("Помилка при закритті");
  }
};

const formatTime = (d) => new Date(d).toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
const formatDate = (d) => new Date(d).toLocaleDateString('uk-UA', { day: 'numeric', month: 'numeric' });
const translateType = (type) => {
  const map = { 'guest_car': 'Автомобіль', 'guest_foot': 'Гість', 'taxi': 'Таксі', 'delivery': 'Доставка' };
  return map[type] || type;
};
const getTypeColor = (type) => {
  const map = { 'guest': 'bg-blue-200', 'taxi': 'bg-yellow-300', 'delivery': 'bg-orange-300', 'service': 'bg-gray-300' };
  return map[type] || 'bg-white';
};

onMounted(() => {
  updateDate();
  fetchRequests();

  setInterval(updateDate, 60000);
  interval = setInterval(fetchRequests, 60000);
});

onUnmounted(() => {
  if (interval) clearInterval(interval);
});
</script>
