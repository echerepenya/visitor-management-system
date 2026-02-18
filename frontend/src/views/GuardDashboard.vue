<template>
  <div class="w-full max-w-7xl mx-auto p-4 pb-20 font-sans">

    <header class="flex justify-between items-center mb-6 md:mb-8 border-b-4 border-black pb-4">
      <div>
        <h1 class="text-2xl md:text-3xl font-black text-gray-900 uppercase tracking-tighter">ЖУРНАЛ ОХОРОНИ</h1>
        <p class="text-gray-600 font-bold text-xs md:text-sm mt-1">Оновлюється автоматично • {{ currentDate }}</p>
      </div>
      <button @click="auth.logout()"
              class="bg-red-600 text-white md:text-black font-bold uppercase text-sm md:text-base px-4 py-2 md:px-6 md:py-3 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all">
        Вийти
      </button>
    </header>

    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-4 border-black"></div>
    </div>

    <div v-else>

      <div class="block md:hidden space-y-4">
        <div v-for="req in sortedRequests" :key="req.id"
             @click="req.status !== 'completed' && openConfirm(req)"
             class="bg-white p-4 rounded-lg border-4 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] active:translate-y-1 active:shadow-none transition-all"
             :class="req.status === 'completed' ? 'opacity-70 bg-gray-100' : 'cursor-pointer active:bg-yellow-50'">

          <div class="flex justify-between items-start mb-3">
             <span :class="getTypeColor(req.type)"
                   class="py-1 px-2 border border-black text-[10px] font-black uppercase shadow-[1px_1px_0px_0px_rgba(0,0,0,0.2)]">
                {{ translateType(req.type) }}
             </span>
             <span class="text-xs font-bold text-gray-400">{{ formatTime(req.created_at) }}</span>
          </div>

          <div class="text-xl font-black uppercase tracking-wide mb-2"
               :class="{ 'line-through text-gray-400': req.status === 'completed' }">
            {{ req.value }}
          </div>

          <div class="border-t-2 border-gray-100 pt-2 mt-2">
            <div class="font-bold text-sm text-gray-900">{{ req.user.full_name || 'Гість' }}</div>
            <div v-if="req.user.apartment" class="text-xs text-gray-500">
              кв. {{ req.user.apartment.number }} • {{ req.user.apartment.building.address }}
            </div>
          </div>
        </div>

        <div v-if="requests.length === 0" class="text-center py-10 text-gray-400 font-bold uppercase">
          Немає активних заявок
        </div>
      </div>

      <div class="hidden md:block overflow-hidden border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] bg-white rounded-lg">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-black text-white uppercase text-sm leading-normal">
              <th class="py-4 px-6 font-bold w-32 text-center">Тип</th>
              <th class="py-4 px-6 font-bold w-1/4">Гість / Авто</th>
              <th class="py-4 px-6 font-bold">Автор заявки</th>
              <th class="py-4 px-6 font-bold w-48 text-right">Час</th>
              <th class="py-4 px-6 font-bold w-24 text-center">Дія</th>
            </tr>
          </thead>
          <tbody class="text-gray-900 text-base font-bold">

            <tr v-for="req in sortedRequests" :key="req.id"
                @click="req.status !== 'completed' && openConfirm(req)"
                class="border-b-4 border-black last:border-b-0 transition-all duration-200"
                :class="req.status === 'completed' ? 'bg-gray-100 text-gray-400 cursor-default' : 'cursor-pointer hover:bg-yellow-50 group'">

              <td class="py-4 px-6 text-center border-r-2 border-gray-100 transition-colors"
                  :class="{ 'opacity-50 grayscale': req.status === 'completed' }">
                <span :class="getTypeColor(req.type)"
                      class="inline-block py-2 px-3 border-2 border-black text-xs font-black uppercase shadow-[2px_2px_0px_0px_rgba(0,0,0,0.2)] whitespace-nowrap">
                  {{ translateType(req.type) }}
                </span>
              </td>

              <td class="py-4 px-6 border-r-2 border-gray-100 transition-colors">
                <div class="text-2xl font-black uppercase tracking-wide"
                     :class="{ 'line-through decoration-4 decoration-black/30': req.status === 'completed' }">
                  {{ req.value }}
                </div>
              </td>

              <td class="py-4 px-6 border-r-2 border-gray-100 transition-colors">
                <div class="flex flex-col">
                  <span class="font-bold text-gray-900 text-lg">
                    {{ req.user.full_name || 'Гість' }}
                  </span>

                  <a :href="'tel:+' + req.user.phone_number"
                     class="text-sm text-blue-600 hover:text-blue-800 hover:underline font-bold w-max"
                     @click.stop>
                    +{{ req.user.phone_number }}
                  </a>

                  <span v-if="req.user.apartment" class="text-xs text-gray-500 mt-1 font-medium">
                    {{ req.user.apartment.building.address }}, кв. {{ req.user.apartment.number }}
                  </span>
                  <span v-else class="text-xs text-gray-400 mt-1 font-medium">
                    Адреса не вказана
                  </span>
                </div>
              </td>

              <td class="py-4 px-6 border-r-2 border-gray-100 transition-colors text-right">
                <div class="text-xl font-mono font-bold">{{ formatTime(req.created_at) }}</div>
                <div class="text-xs uppercase font-bold opacity-60">{{ formatDate(req.created_at) }}</div>
              </td>

              <td class="py-4 px-6 text-center">
                <div v-if="req.status !== 'completed'"
                     class="w-12 h-12 mx-auto bg-black text-white flex items-center justify-center rounded-full group-hover:scale-110 group-hover:bg-green-600 transition-all shadow-[2px_2px_0px_0px_rgba(0,0,0,0.3)]">
                  <span class="text-2xl pb-1">➝</span>
                </div>

                <div v-else
                     class="w-12 h-12 mx-auto border-4 border-gray-300 text-gray-300 flex items-center justify-center rounded-full font-black text-xl bg-gray-50">
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
    </div>

    <div v-if="selectedRequest"
         class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto"
         @click.self="selectedRequest = null">

      <div class="bg-white border-4 border-black p-6 md:p-8 max-w-md w-full shadow-[12px_12px_0px_0px_rgba(255,255,255,1)] relative my-8">

        <button @click="selectedRequest = null" class="absolute top-2 right-2 text-3xl font-bold hover:text-red-600 px-2 leading-none">&times;</button>

        <h2 class="text-2xl md:text-3xl font-black mb-6 uppercase border-b-4 border-yellow-300 inline-block">
          Пропустити?
        </h2>

        <div class="bg-gray-100 p-4 border-2 border-black mb-6 text-center">
          <p class="text-xs text-gray-500 uppercase font-bold mb-1">Гість / Номер авто:</p>
          <p class="text-3xl md:text-4xl font-black uppercase break-all">{{ selectedRequest.value }}</p>
        </div>

        <div class="border-t-2 border-gray-300 pt-4 mt-4">
          <p class="text-xs text-gray-400 uppercase font-bold mb-2">Автор заявки:</p>

          <div class="bg-gray-50 p-4 rounded-lg border-2 border-gray-200">
            <div class="flex items-center justify-between mb-3">
              <span class="font-bold text-xl text-gray-900 leading-none">
                {{ selectedRequest.user.full_name || 'Не вказано' }}
              </span>
            </div>

            <div class="space-y-2">
              <div class="flex items-center text-gray-700">
                <span class="mr-2 text-lg">📞</span>
                <a :href="'tel:+' + selectedRequest.user.phone_number" class="font-bold text-blue-600 hover:underline text-lg">
                  +{{ selectedRequest.user.phone_number }}
                </a>
              </div>

              <div v-if="selectedRequest.user.apartment" class="flex items-start text-gray-700">
                <span class="mr-2 text-lg">🏠</span>
                <span class="font-medium text-sm leading-tight pt-1">
                  {{ selectedRequest.user.apartment.building.address }}, <br>
                  кв. <span class="font-bold text-black">{{ selectedRequest.user.apartment.number }}</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="selectedRequest.comment" class="mt-4">
           <p class="text-xs text-gray-400 uppercase font-bold mb-1">Коментар:</p>
           <div class="bg-yellow-50 p-3 rounded border-l-4 border-yellow-400 italic text-gray-800 font-medium text-sm">
             "{{ selectedRequest.comment }}"
           </div>
        </div>

        <div class="grid grid-cols-2 gap-4 mt-8">
          <button @click="selectedRequest = null"
                  class="border-2 border-black py-4 font-black uppercase hover:bg-gray-200 transition-colors text-sm md:text-base">
            Скасувати
          </button>
          <button @click="closeRequest"
                  class="bg-green-600 text-white border-2 border-black py-4 font-black uppercase hover:bg-green-700 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all text-sm md:text-base">
            Так, пропустив
          </button>
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
  return [...requests.value].sort((a, b) => {
    const weightA = a.status === 'new' ? 0 : 1;
    const weightB = b.status === 'new' ? 0 : 1;

    if (weightA !== weightB) {
      return weightA - weightB;
    }

    return new Date(b.created_at) - new Date(a.created_at);
  });
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
