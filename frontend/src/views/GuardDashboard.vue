<template>
  <div class="w-full max-w-7xl mx-auto p-4 pb-20 font-sans">
    <header class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 border-b-4 border-black pb-4 gap-4">
      <div>
        <div class="flex items-center gap-3">
          <h1 class="text-2xl md:text-3xl font-black text-gray-900 uppercase tracking-tighter">ЖУРНАЛ ОХОРОНИ</h1>
          <span :class="isConnected ? 'bg-green-500' : 'bg-red-500 animate-pulse'"
                class="w-4 h-4 rounded-full border-2 border-black"
                :title="isConnected ? 'Підключено до сервера' : 'Втрачено зв\'язок...'">
          </span>
        </div>
        <p class="text-gray-600 font-bold text-xs md:text-sm mt-1">Оновлюється автоматично • {{ currentDate }}</p>
      </div>
      <div class="flex gap-2 md:gap-4 w-full md:w-auto">
        <button @click="toggleSound"
                class="flex-1 md:flex-none bg-yellow-300 text-black font-bold uppercase text-sm md:text-base px-4 py-2 md:px-6 md:py-3 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all">
          {{ isMuted ? '🔇 Вимкнено' : '🔊 Звук' }}
        </button>
        <button v-if="isTelegram"
                @click="closeWebApp"
                class="flex-1 md:flex-none bg-gray-200 text-black font-bold uppercase text-sm md:text-base px-4 py-2 md:px-6 md:py-3 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all">
          Закрити
        </button>
        <button v-else
                @click="auth.logout()"
                class="flex-1 md:flex-none bg-red-600 text-white font-bold uppercase text-sm md:text-base px-4 py-2 md:px-6 md:py-3 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all">
          Вийти
        </button>
      </div>
    </header>

    <!-- Tabs Navigation -->
    <div class="flex space-x-2 md:space-x-4 mb-6">
      <button @click="activeTab = 'passes'"
              :class="activeTab === 'passes' ? 'bg-black text-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-white text-black border-2 border-black hover:bg-gray-100'"
              class="flex-1 md:flex-none font-black uppercase text-xs md:text-sm px-3 py-2 transition-all rounded">
        🎫 Перепустки
      </button>
      <button @click="activeTab = 'parking'"
              :class="activeTab === 'parking' ? 'bg-black text-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' : 'bg-white text-black border-2 border-black hover:bg-gray-100'"
              class="flex-1 md:flex-none font-black uppercase text-xs md:text-sm px-3 py-2 transition-all rounded">
        🅿️ Гостьова Парковка
      </button>
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-4 border-black"></div>
    </div>

    <div v-else>
      <!-- TAB 1: PASSES -->
      <div v-if="activeTab === 'passes'">
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
              <tr v-for="req in sortedPassRequests" :key="req.id"
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
                    <a :href="'tel:+' + req.user.phone_number" class="text-sm text-blue-600 hover:text-blue-800 hover:underline font-bold w-max" @click.stop>
                      +{{ req.user.phone_number }}
                    </a>
                    <span v-if="req.user.apartment" class="text-xs text-gray-500 mt-1 font-medium">
                      {{ req.user.apartment.building.address }}, кв. {{ req.user.apartment.number }}
                    </span>
                    <span v-else class="text-xs text-gray-400 mt-1 font-medium">Адреса не вказана</span>
                  </div>
                </td>
                <td class="py-4 px-6 border-r-2 border-gray-100 transition-colors text-right">
                  <template v-if="req.status === 'completed' && req.updated_at">
                    <div class="text-xl font-mono font-bold text-green-700">{{ formatTime(req.updated_at) }}</div>
                    <div class="text-[10px] uppercase font-black opacity-60">Пропущено: {{ formatDate(req.updated_at) }}</div>
                  </template>
                  <template v-else>
                    <div class="text-xl font-mono font-bold">{{ formatTime(req.created_at) }}</div>
                    <div class="text-[10px] uppercase font-black opacity-60">Створено: {{ formatDate(req.created_at) }}</div>
                  </template>
                </td>
                <td class="py-4 px-6 text-center">
                  <div v-if="req.status !== 'completed'"
                       class="w-12 h-12 mx-auto bg-black text-white flex items-center justify-center rounded-full group-hover:scale-110 group-hover:bg-green-600 transition-all shadow-[2px_2px_0px_0px_rgba(0,0,0,0.3)]">
                    <span class="text-2xl pb-1">➝</span>
                  </div>
                  <div v-else class="w-12 h-12 mx-auto border-4 border-gray-300 text-gray-300 flex items-center justify-center rounded-full font-black text-xl bg-gray-50">✓</div>
                </td>
              </tr>
              <tr v-if="passRequests.length === 0">
                <td colspan="5" class="py-20 text-center bg-gray-50 text-xl font-black uppercase text-gray-400">Немає заявок</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Mobile View: Passes -->
        <div class="md:hidden space-y-4 mt-4">
          <div v-for="req in sortedPassRequests" :key="'mob_' + req.id"
               @click="req.status !== 'completed' && openConfirm(req)"
               class="bg-white border-4 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] p-4 relative"
               :class="{ 'opacity-60 grayscale': req.status === 'completed' }">
            <div class="flex justify-between items-start mb-2">
              <span :class="getTypeColor(req.type)" class="inline-block py-1 px-2 border-2 border-black text-[10px] font-black uppercase shadow-[2px_2px_0px_0px_rgba(0,0,0,0.2)]">
                {{ translateType(req.type) }}
              </span>
              <div class="text-right">
                <div class="text-sm font-mono font-black">{{ formatTime(req.status === 'completed' && req.updated_at ? req.updated_at : req.created_at) }}</div>
              </div>
            </div>
            <div class="text-2xl font-black uppercase tracking-wide mb-2" :class="{ 'line-through decoration-4 decoration-black/30': req.status === 'completed' }">
              {{ req.value }}
            </div>
            <div class="text-sm font-bold text-gray-900">
              {{ req.user.full_name || 'Гість' }}
            </div>
            <a :href="'tel:+' + req.user.phone_number" class="text-sm text-blue-600 hover:underline font-bold block" @click.stop>
              +{{ req.user.phone_number }}
            </a>
            <div v-if="req.user.apartment" class="text-xs text-gray-500 mt-1 font-medium mb-2">
              {{ req.user.apartment.building.address }}, кв. {{ req.user.apartment.number }}
            </div>
            <div v-else class="text-xs text-gray-400 mt-1 font-medium mb-2">Адреса не вказана</div>
            <div v-if="req.status !== 'completed'" class="absolute bottom-4 right-4 w-10 h-10 bg-black text-white flex items-center justify-center rounded-full font-bold shadow-[2px_2px_0px_0px_rgba(0,0,0,0.3)]">➝</div>
            <div v-else class="absolute bottom-4 right-4 w-10 h-10 border-2 border-gray-300 text-gray-400 flex items-center justify-center rounded-full font-black bg-gray-50">✓</div>
          </div>
          <div v-if="passRequests.length === 0" class="p-8 text-center bg-gray-50 text-lg font-black uppercase text-gray-400 border-4 border-dashed border-gray-300">Немає заявок</div>
        </div>
      </div>

      <!-- TAB 2: PARKING -->
      <div v-if="activeTab === 'parking'">
        <!-- Parking Status Widget -->
        <div class="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-purple-900 text-white p-4 rounded-lg border-4 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex items-center justify-between">
            <div class="flex-1">
              <div class="text-xs uppercase font-black tracking-wider text-purple-200">Гостьова парковка</div>
              
              <div v-if="!isEditingParking" class="text-3xl font-black mt-1 flex items-center gap-2">
                <span>{{ parkingStatus.free_spots }} <span class="text-base font-normal text-purple-200">/ {{ parkingStatus.total_spots }} вільних</span></span>
                <button @click="startEditingParking" title="Змінити кількість" class="text-sm bg-purple-700 hover:bg-purple-600 px-2 py-1 rounded border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] ml-2">✎</button>
              </div>
              
              <div v-else class="mt-1 flex items-center gap-2">
                <input type="number" v-model.number="editFreeSpotsValue" min="0" :max="parkingStatus.total_spots" 
                       class="w-20 bg-white text-black font-bold text-xl p-1 border-2 border-black rounded text-center h-10">
                <button @click="saveParkingEdit" :disabled="isSubmitting" class="bg-green-500 text-black font-bold h-10 px-3 rounded border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:bg-green-400">✓</button>
                <button @click="isEditingParking = false" class="bg-red-500 text-black font-bold h-10 px-3 rounded border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:bg-red-400">✗</button>
              </div>
            </div>
            <div class="text-4xl ml-2">🅿️</div>
          </div>

          <div :class="[
                 parkingStatus.keyfob.overdue ? 'bg-red-600 text-white animate-pulse' :
                 parkingStatus.keyfob.state === 'WITH_GUEST' ? 'bg-amber-400 text-black' :
                 'bg-green-600 text-white'
               ]"
               class="md:col-span-2 p-4 rounded-lg border-4 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex flex-col md:flex-row items-start md:items-center justify-between gap-3 transition-all">
            <div>
              <div class="flex items-center gap-2">
                <span class="text-2xl">🔑</span>
                <span class="font-black uppercase tracking-wide text-lg">
                  {{ parkingStatus.keyfob.state === 'WITH_GUARD' ? 'Брелок на Посту 2' : 'Брелок видано гостю' }}
                </span>
                <span v-if="parkingStatus.keyfob.overdue" class="bg-black text-white text-xs font-black uppercase px-2 py-1 rounded border border-white">
                  ⚠️ УВАГА! > 30 хв
                </span>
              </div>
              <p v-if="parkingStatus.keyfob.state === 'WITH_GUEST' && parkingStatus.keyfob.guest_info" class="text-sm font-bold mt-1">
                Авто: <span class="uppercase underline font-black text-base">{{ parkingStatus.keyfob.guest_info.license_plate }}</span>
                <span v-if="parkingStatus.keyfob.guest_info.apartment_number"> (кв. {{ parkingStatus.keyfob.guest_info.apartment_number }})</span>
              </p>
              <p v-else class="text-xs font-medium opacity-90 mt-1">Брелок вільний для видачі наступній машині.</p>
            </div>
            <button v-if="parkingStatus.keyfob.state === 'WITH_GUEST'"
                    @click="showResetModal = true"
                    class="bg-black text-white hover:bg-gray-800 font-black uppercase text-xs px-3 py-2 border-2 border-white shadow-[2px_2px_0px_0px_rgba(255,255,255,1)] transition-all whitespace-nowrap">
              ⚠️ Скинути брелок
            </button>
          </div>
        </div>

        <!-- Parking Table -->
        <div class="hidden md:block overflow-hidden border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] bg-white rounded-lg">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-black text-white uppercase text-sm leading-normal">
                <th class="py-4 px-6 font-bold w-36 text-center">Стан</th>
                <th class="py-4 px-6 font-bold w-1/4">Номер Авто</th>
                <th class="py-4 px-6 font-bold">Автор заявки</th>
                <th class="py-4 px-6 font-bold w-48 text-right">Час</th>
                <th class="py-4 px-6 font-bold w-48 text-center">Дія</th>
              </tr>
            </thead>
            <tbody class="text-gray-900 text-base font-bold">
              <tr v-for="req in sortedParkingRequests" :key="'p_' + req.id"
                  class="border-b-4 border-black last:border-b-0 transition-all duration-200"
                  :class="req.status === 'completed' || req.status === 'expired' ? 'bg-gray-100 text-gray-400' : 'hover:bg-purple-50 group'">
                <td class="py-4 px-6 text-center border-r-2 border-gray-100">
                  <span class="text-[10px] font-extrabold uppercase px-2 py-1 border border-black rounded"
                        :class="getParkingStatusClass(req.status)">
                    {{ getParkingStatusLabel(req.status) }}
                  </span>
                </td>
                <td class="py-4 px-6 border-r-2 border-gray-100">
                  <div class="text-2xl font-black uppercase tracking-wide"
                       :class="{ 'line-through decoration-4 decoration-black/30': req.status === 'completed' || req.status === 'expired' }">
                    {{ req.license_plate }}
                  </div>
                </td>
                <td class="py-4 px-6 border-r-2 border-gray-100">
                  <div class="flex flex-col">
                    <span class="font-bold text-gray-900 text-lg">{{ req.user.full_name || 'Гість' }}</span>
                    <a :href="'tel:+' + req.user.phone_number" class="text-sm text-blue-600 hover:text-blue-800 hover:underline font-bold w-max">
                      +{{ req.user.phone_number }}
                    </a>
                    <span v-if="req.user.apartment" class="text-xs text-gray-500 mt-1 font-medium">
                      {{ req.user.apartment.building.address }}, кв. {{ req.user.apartment.number }}
                    </span>
                    <span v-else class="text-xs text-gray-400 mt-1 font-medium">Адреса не вказана</span>
                  </div>
                </td>
                <td class="py-4 px-6 border-r-2 border-gray-100 text-right">
                  <div class="text-xl font-mono font-bold">{{ formatTime(req.created_at) }}</div>
                  <div class="text-[10px] uppercase font-black opacity-60">Створено: {{ formatDate(req.created_at) }}</div>
                </td>
                <td class="py-4 px-6 text-center">
                  <button v-if="req.status === 'new'"
                          @click="openParkingConfirm(req, 'issue_entry')"
                          :disabled="parkingStatus.keyfob.state === 'WITH_GUEST' || isSubmitting"
                          class="bg-green-600 text-white font-black uppercase text-xs px-3 py-2 border-2 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-y-0.5 hover:shadow-none transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                    🟢 Видати брелок
                  </button>
                  <button v-else-if="req.status === 'keyfob_issued_entry'"
                          @click="openParkingConfirm(req, 'return_entry')"
                          :disabled="isSubmitting"
                          class="bg-yellow-300 text-black font-black uppercase text-xs px-3 py-2 border-2 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-y-0.5 hover:shadow-none transition-all">
                    📥 Запарковано
                  </button>
                  <button v-else-if="req.status === 'parked'"
                          @click="openParkingConfirm(req, 'issue_exit')"
                          :disabled="parkingStatus.keyfob.state === 'WITH_GUEST' || isSubmitting"
                          class="bg-blue-600 text-white font-black uppercase text-xs px-3 py-2 border-2 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-y-0.5 hover:shadow-none transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                    🟢 Брелок на виїзд
                  </button>
                  <button v-else-if="req.status === 'keyfob_issued_exit'"
                          @click="openParkingConfirm(req, 'return_exit')"
                          :disabled="isSubmitting"
                          class="bg-green-600 text-white font-black uppercase text-xs px-3 py-2 border-2 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-y-0.5 hover:shadow-none transition-all">
                    📥 Виїхав
                  </button>
                  <div v-else-if="req.status === 'completed'" class="w-10 h-10 mx-auto border-4 border-gray-300 text-gray-300 flex items-center justify-center rounded-full font-black text-xl bg-gray-50">✓</div>
                  <div v-else-if="req.status === 'expired'" class="w-10 h-10 mx-auto border-4 border-red-300 text-red-400 flex items-center justify-center rounded-full font-black text-xl bg-red-50">X</div>
                </td>
              </tr>
              <tr v-if="parkingRequests.length === 0">
                <td colspan="5" class="py-20 text-center bg-gray-50 text-xl font-black uppercase text-gray-400">Немає заявок на парковку</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Mobile View: Parking -->
        <div class="md:hidden space-y-4 mt-4">
          <div v-for="req in sortedParkingRequests" :key="'p_mob_' + req.id"
               class="bg-white border-4 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] p-4"
               :class="{ 'opacity-60 grayscale': req.status === 'completed' || req.status === 'expired' }">
            <div class="flex justify-between items-start mb-2">
              <span class="text-[10px] font-extrabold uppercase px-2 py-1 border border-black rounded" :class="getParkingStatusClass(req.status)">
                {{ getParkingStatusLabel(req.status) }}
              </span>
              <div class="text-sm font-mono font-black">{{ formatTime(req.created_at) }}</div>
            </div>
            <div class="text-2xl font-black uppercase tracking-wide mb-2" :class="{ 'line-through decoration-4 decoration-black/30': req.status === 'completed' || req.status === 'expired' }">
              {{ req.license_plate }}
            </div>
            <div class="text-sm font-bold text-gray-900">
              {{ req.user.full_name || 'Гість' }} 
              <a :href="'tel:+' + req.user.phone_number" class="text-blue-600 hover:underline inline-block ml-1">+{{ req.user.phone_number }}</a>
            </div>
            <div v-if="req.user.apartment" class="text-xs text-gray-500 mt-1 font-medium mb-2">
              {{ req.user.apartment.building.address }}, кв. {{ req.user.apartment.number }}
            </div>
            <div v-else class="text-xs text-gray-400 mt-1 font-medium mb-2">Адреса не вказана</div>
            
            <div class="mt-4 flex flex-col gap-2">
                  <button v-if="req.status === 'new'"
                          @click="openParkingConfirm(req, 'issue_entry')"
                          :disabled="parkingStatus.keyfob.state === 'WITH_GUEST' || isSubmitting"
                          class="w-full bg-green-600 text-white font-black uppercase text-sm px-4 py-3 border-2 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50 transition-all">
                    🟢 Видати брелок
                  </button>
                  <button v-else-if="req.status === 'keyfob_issued_entry'"
                          @click="openParkingConfirm(req, 'return_entry')"
                          :disabled="isSubmitting"
                          class="w-full bg-yellow-300 text-black font-black uppercase text-sm px-4 py-3 border-2 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50 transition-all">
                    📥 Запарковано
                  </button>
                  <button v-else-if="req.status === 'parked'"
                          @click="openParkingConfirm(req, 'issue_exit')"
                          :disabled="parkingStatus.keyfob.state === 'WITH_GUEST' || isSubmitting"
                          class="w-full bg-blue-600 text-white font-black uppercase text-sm px-4 py-3 border-2 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50 transition-all">
                    🟢 Брелок на виїзд
                  </button>
                  <button v-else-if="req.status === 'keyfob_issued_exit'"
                          @click="openParkingConfirm(req, 'return_exit')"
                          :disabled="isSubmitting"
                          class="w-full bg-green-600 text-white font-black uppercase text-sm px-4 py-3 border-2 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50 transition-all">
                    📥 Виїхав
                  </button>
            </div>
          </div>
          <div v-if="parkingRequests.length === 0" class="p-8 text-center bg-gray-50 text-lg font-black uppercase text-gray-400 border-4 border-dashed border-gray-300">Немає заявок на парковку</div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <!-- Pass Confirm Modal -->
    <div v-if="selectedRequest" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto" @click.self="selectedRequest = null">
      <div class="bg-white border-4 border-black p-6 md:p-8 max-w-md w-full shadow-[12px_12px_0px_0px_rgba(255,255,255,1)] relative my-8">
        <button @click="selectedRequest = null" :disabled="isSubmitting" class="absolute top-2 right-2 text-3xl font-bold hover:text-red-600 px-2 leading-none">&times;</button>
        <h2 class="text-2xl md:text-3xl font-black mb-6 uppercase border-b-4 border-yellow-300 inline-block">Пропустити?</h2>
        <div class="bg-gray-100 p-4 border-2 border-black mb-6 text-center">
          <p class="text-xs text-gray-500 uppercase font-bold mb-1">Гість / Номер авто:</p>
          <p class="text-3xl md:text-4xl font-black uppercase break-all">{{ selectedRequest.value }}</p>
        </div>
        <div class="grid grid-cols-2 gap-4 mt-8">
          <button @click="selectedRequest = null" :disabled="isSubmitting" class="border-2 border-black py-4 font-black uppercase hover:bg-gray-200 transition-colors text-sm md:text-base disabled:opacity-50">Назад</button>
          <button @click="closeRequest" :disabled="isSubmitting" class="bg-green-600 text-white border-2 border-black py-4 font-black uppercase hover:bg-green-700 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all text-sm md:text-base flex items-center justify-center disabled:opacity-70">
            {{ isSubmitting ? 'Обробка...' : 'Так, пропустив' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Parking Action Confirm Modal -->
    <div v-if="selectedParkingRequest" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto" @click.self="selectedParkingRequest = null">
      <div class="bg-white border-4 border-black p-6 md:p-8 max-w-md w-full shadow-[12px_12px_0px_0px_rgba(255,255,255,1)] relative my-8">
        <button @click="selectedParkingRequest = null" :disabled="isSubmitting" class="absolute top-2 right-2 text-3xl font-bold hover:text-red-600 px-2 leading-none">&times;</button>
        
        <h2 v-if="parkingActionType === 'issue_entry' || parkingActionType === 'issue_exit'" class="text-2xl md:text-3xl font-black mb-6 uppercase border-b-4 border-green-400 inline-block">Видати брелок?</h2>
        <h2 v-else class="text-2xl md:text-3xl font-black mb-6 uppercase border-b-4 border-yellow-300 inline-block">Повернути брелок?</h2>
        
        <div class="bg-gray-100 p-4 border-2 border-black mb-6 text-center">
          <p class="text-xs text-gray-500 uppercase font-bold mb-1">Номер авто:</p>
          <p class="text-3xl md:text-4xl font-black uppercase break-all">{{ selectedParkingRequest.license_plate }}</p>
        </div>
        
        <p v-if="parkingActionType === 'issue_entry'" class="font-bold text-gray-700 mb-4 text-center">Підтвердіть, що ви фізично видали брелок гостю для заїзду.</p>
        <p v-if="parkingActionType === 'return_entry'" class="font-bold text-gray-700 mb-4 text-center">Гість запаркувався. Підтвердіть, що брелок повернуто вам на пост.</p>
        <p v-if="parkingActionType === 'issue_exit'" class="font-bold text-gray-700 mb-4 text-center">Підтвердіть, що ви видали брелок гостю для виїзду.</p>
        <p v-if="parkingActionType === 'return_exit'" class="font-bold text-gray-700 mb-4 text-center">Гість виїхав. Підтвердіть, що ви забрали брелок.</p>

        <div class="grid grid-cols-2 gap-4 mt-6">
          <button @click="selectedParkingRequest = null" :disabled="isSubmitting" class="border-2 border-black py-4 font-black uppercase hover:bg-gray-200 transition-colors text-sm md:text-base disabled:opacity-50">Назад</button>
          
          <button v-if="parkingActionType.startsWith('issue')" @click="confirmParkingAction" :disabled="isSubmitting" class="bg-green-600 text-white border-2 border-black py-4 font-black uppercase hover:bg-green-700 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all text-sm flex items-center justify-center disabled:opacity-70">
            {{ isSubmitting ? 'Обробка...' : 'Так, видано' }}
          </button>
          
          <button v-else @click="confirmParkingAction" :disabled="isSubmitting" class="bg-yellow-300 text-black border-2 border-black py-4 font-black uppercase hover:bg-yellow-400 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all text-sm flex items-center justify-center disabled:opacity-70">
            {{ isSubmitting ? 'Обробка...' : 'Так, забрано' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Emergency Keyfob Reset Modal -->
    <div v-if="showResetModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50" @click.self="showResetModal = false">
      <div class="bg-white border-4 border-black p-6 max-w-md w-full shadow-[12px_12px_0px_0px_rgba(255,255,255,1)] relative">
        <h2 class="text-2xl font-black mb-4 uppercase text-red-600 border-b-4 border-red-600 inline-block">⚠️ Скинути стан брелока?</h2>
        <p class="font-bold text-gray-800 mb-6 text-sm">Ця дія примусово поверне брелок у стан «На Посту 2». Використовуйте тільки якщо брелок повернули в обхід системи чи відбувся збій.</p>
        <div class="grid grid-cols-2 gap-4">
          <button @click="showResetModal = false" :disabled="isSubmitting" class="border-2 border-black py-3 font-black uppercase hover:bg-gray-200 text-sm">Скасувати</button>
          <button @click="handleResetKeyfob" :disabled="isSubmitting" class="bg-red-600 text-white border-2 border-black py-3 font-black uppercase hover:bg-red-700 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none text-sm">Скинути</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import requestsApi from '@/api/requests';
import parkingApi from '@/api/parking';
import { useWebsocket } from '@/composables/useWebsocket';

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

const activeTab = ref(route.query.tab === 'parking' ? 'parking' : 'passes');
const passRequests = ref([]);
const parkingRequests = ref([]);
const loading = ref(true);
const selectedRequest = ref(null);
const selectedParkingRequest = ref(null);
const parkingActionType = ref('');
const showResetModal = ref(false);
const currentDate = ref('');
let clockInterval = null;

const parkingStatus = ref({
  total_spots: 11, occupied_spots: 0, free_spots: 11,
  keyfob: { state: 'WITH_GUARD', request_id: null, issued_at: null, overdue: false, guest_info: null }
});

const isMuted = ref(false);
const audio = new Audio('/sounds/new-pass-request-notification.mp3');

const isTelegram = computed(() => {
  const tg = window.Telegram?.WebApp;
  return !!(tg && tg.initData && tg.initData.length > 0);
});

const closeWebApp = () => window.Telegram?.WebApp?.close();

const toggleSound = () => {
  isMuted.value = !isMuted.value;
  if (!isMuted.value) playNotification();
};

const playNotification = () => {
  if (!isMuted.value) {
    audio.currentTime = 0;
    audio.play().catch(err => console.warn("Звук заблоковано:", err));
  }
};

const updateDate = () => {
  const date = new Date();
  const options = { weekday: 'long', day: 'numeric', month: 'long' };
  let dateString = date.toLocaleDateString('uk-UA', options);
  currentDate.value = dateString.charAt(0).toUpperCase() + dateString.slice(1);
};

const sortedPassRequests = computed(() => {
  return [...passRequests.value].sort((a, b) => {
    const weightA = a.status === 'new' ? 0 : 1;
    const weightB = b.status === 'new' ? 0 : 1;
    if (weightA !== weightB) return weightA - weightB;
    return new Date(b.created_at) - new Date(a.created_at);
  });
});

const sortedParkingRequests = computed(() => {
  const priority = { 'new': 0, 'keyfob_issued_entry': 1, 'parked': 2, 'keyfob_issued_exit': 3, 'completed': 4, 'expired': 5 };
  return [...parkingRequests.value].sort((a, b) => {
    const wA = priority[a.status] ?? 99;
    const wB = priority[b.status] ?? 99;
    if (wA !== wB) return wA - wB;
    return new Date(b.created_at) - new Date(a.created_at);
  });
});

const fetchData = async () => {
  try {
    const [reqsRes, parkingReqsRes, parkingStatusRes] = await Promise.all([
      requestsApi.getActive(),
      parkingApi.getActiveRequests(),
      parkingApi.getStatus()
    ]);
    passRequests.value = reqsRes.data;
    parkingRequests.value = parkingReqsRes.data;
    if (parkingStatusRes.data) {
      parkingStatus.value = parkingStatusRes.data;
      if (parkingStatus.value.keyfob.overdue) playNotification();
    }
  } catch (e) {
    console.error("Помилка API:", e);
  } finally {
    loading.value = false;
  }
};

const isSubmitting = ref(false);
const errorMessage = ref(null);

const isEditingParking = ref(false);
const editFreeSpotsValue = ref(0);

const startEditingParking = () => {
  editFreeSpotsValue.value = parkingStatus.value.free_spots;
  isEditingParking.value = true;
};

const saveParkingEdit = async () => {
  if (isSubmitting.value) return;
  isSubmitting.value = true;
  try {
    const res = await parkingApi.overrideSpots(editFreeSpotsValue.value);
    parkingStatus.value = res.data;
    isEditingParking.value = false;
  } catch (e) {
    alert(e.response?.data?.detail || "Помилка");
  } finally {
    isSubmitting.value = false;
  }
};

const closeRequest = async () => {
  if (!selectedRequest.value || isSubmitting.value) return;
  isSubmitting.value = true;
  errorMessage.value = null;
  try {
    await requestsApi.complete(selectedRequest.value.id);
    selectedRequest.value = null;
    await fetchData();
  } catch (e) {
    errorMessage.value = e.response?.data?.detail || "Помилка при закритті заявки";
    if (e.response?.status === 400) setTimeout(() => fetchData(), 1500);
  } finally {
    isSubmitting.value = false;
  }
};

const openParkingConfirm = (req, type) => {
  selectedParkingRequest.value = req;
  parkingActionType.value = type;
};

const confirmParkingAction = async () => {
  if (!selectedParkingRequest.value || isSubmitting.value) return;
  isSubmitting.value = true;
  try {
    const isIssue = parkingActionType.value.startsWith('issue');
    if (isIssue) {
      await parkingApi.issueKeyfob(selectedParkingRequest.value.id);
    } else {
      await parkingApi.returnKeyfob(selectedParkingRequest.value.id);
    }
    selectedParkingRequest.value = null;
    await fetchData();
  } catch (e) {
    alert(e.response?.data?.detail || "Помилка");
  } finally {
    isSubmitting.value = false;
  }
};

const handleResetKeyfob = async () => {
  if (isSubmitting.value) return;
  isSubmitting.value = true;
  try {
    await parkingApi.resetKeyfob();
    showResetModal.value = false;
    await fetchData();
  } catch (e) {
    alert(e.response?.data?.detail || "Помилка");
  } finally {
    isSubmitting.value = false;
  }
};

const openConfirm = (req) => {
  if (req.status !== 'new') return;
  selectedRequest.value = req;
};

const formatTime = (d) => d ? new Date(d).toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' }) : '';
const formatDate = (d) => d ? new Date(d).toLocaleDateString('uk-UA', { day: 'numeric', month: 'numeric' }) : '';
const translateType = (type) => ({ 'guest_car': 'Автомобіль', 'guest_foot': 'Гість', 'taxi': 'Таксі', 'delivery': 'Доставка' }[type] || type);
const getTypeColor = (type) => ({ 'guest_car': 'bg-blue-200', 'guest_foot': 'bg-green-200', 'taxi': 'bg-yellow-300', 'delivery': 'bg-orange-300' }[type] || 'bg-white');

const getParkingStatusLabel = (status) => {
  const map = { 'new': 'Бронь', 'keyfob_issued_entry': '🔑 На в\'їзді', 'parked': '🅿️ На парковці', 'keyfob_issued_exit': '🔑 На виїзді', 'completed': 'Виїхав', 'expired': 'Скасовано' };
  return map[status] || status;
};

const getParkingStatusClass = (status) => {
  const map = { 'new': 'bg-yellow-100 text-yellow-800', 'keyfob_issued_entry': 'bg-amber-200 text-amber-900', 'parked': 'bg-purple-100 text-purple-900', 'keyfob_issued_exit': 'bg-blue-200 text-blue-900', 'completed': 'bg-green-100 text-green-800', 'expired': 'bg-red-100 text-red-800' };
  return map[status] || 'bg-gray-100 text-gray-800';
};

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
let wsUrl;
const isSecure = window.location.protocol === 'https:';
const protocol = isSecure ? 'wss:' : 'ws:';
if (apiUrl.startsWith('http')) {
  wsUrl = apiUrl.replace(/^http/, 'ws') + '/ws/notifications';
} else {
  wsUrl = `${protocol}//${window.location.host}/ws/notifications`;
}

const { isConnected, connect } = useWebsocket(wsUrl, (data) => {
  if (data.event === 'requests_updated' || data.event === 'parking_requests_updated' || data.event === 'reconnected') {
    fetchData();
    if (data?.new_status === 'new') playNotification();
  }
});

onMounted(() => {
  updateDate();
  fetchData();
  connect();
  clockInterval = setInterval(() => { updateDate(); fetchData(); }, 30000);
});

onUnmounted(() => {
  if (clockInterval) clearInterval(clockInterval);
});
</script>
