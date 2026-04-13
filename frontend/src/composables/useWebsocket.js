import { ref, onUnmounted } from 'vue';

export function useWebsocket(url, onMessageCallback) {
  const ws = ref(null);
  const isConnected = ref(false);
  let reconnectAttempts = 0;
  const maxReconnectDelay = 30000; // Максимум 30 секунд між спробами

  const connect = () => {
    console.log("🔌 Спроба підключення до WebSocket...");
    ws.value = new WebSocket(url);

    ws.value.onopen = () => {
      console.log("✅ WebSocket підключено!");
      isConnected.value = true;
      reconnectAttempts = 0; // Скидаємо лічильник при успіху

      // Сигналізуємо компоненту, що ми відновили зв'язок
      if (onMessageCallback) onMessageCallback({ event: 'reconnected' });
    };

    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (onMessageCallback) onMessageCallback(data);
    };

    ws.value.onclose = () => {
      isConnected.value = false;
      ws.value = null;

      // Розраховуємо затримку (експоненціально зростає)
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), maxReconnectDelay);
      console.log(`❌ Зв'язок розірвано. Реконект через ${delay/1000} сек...`);

      setTimeout(() => {
        reconnectAttempts++;
        connect();
      }, delay);
    };

    ws.value.onerror = (err) => {
      console.error("⚠️ Помилка WebSocket:", err);
      // Не робимо нічого зайвого, бо onerror завжди викликає onclose,
      // де у нас вже написана логіка реконекту
    };
  };

  const sendMessage = (data) => {
    if (ws.value && isConnected.value) {
      ws.value.send(JSON.stringify(data));
    }
  };

  onUnmounted(() => {
    if (ws.value) {
      ws.value.close();
    }
  });

  return { isConnected, connect, sendMessage };
}
