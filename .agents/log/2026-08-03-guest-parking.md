# Гостьова парковка

Статус: wip

## Рішення
Реалізовано функціонал "Гостьова парковка" з такими можливостями:
- Бронювання гостьового паркомісця через Telegram бота.
- Відображення статусу (кількість вільних місць з 11) у боті.
- Панель охорони (Guard Dashboard) доповнена вкладкою парковки, де охорона може бачити заявки, видавати/забирати брелоки (keyfobs).
- Додано повноцінний мобільний вигляд (картки заявок) для Telegram WebApp.
- Впроваджено модальні вікна підтвердження дій для видачі та повернення брелока (запобігання випадковим клікам).
- Зв'язок через Redis Streams для сповіщення охорони про нові заявки.
- База даних доповнена таблицями `guest_parking_requests` та `parking_settings`.

## Чому
Мешканцям потрібно швидко замовляти гостьові паркомісця, а охороні - контролювати їх кількість і видавати брелоки для заїзду. Інтеграція в існуючий Telegram бот як додатковий сервіс є зручним рішенням. Використання Redis Streams для нотифікацій відповідає архітектурі, що вже використовується для перепусток, та забезпечує надійну комунікацію.

## Зачеплені файли/модулі
- **DB**: `backend/src/alembic/versions/*_add_guest_parking_and_keyfob_status.py`, `backend/src/alembic/versions/*_add_parking_settings.py`
- **Backend**: `backend/src/models/parking.py`, `backend/src/routers/parking.py`, `backend/src/services/parking.py`, `backend/src/schemas/parking.py`, `backend/src/redis.py`
- **Frontend**: `frontend/src/api/parking.js`, `frontend/src/views/GuardDashboard.vue`
- **Telegram Bot**: `telegram-bot/src/handlers/parking.py`, `telegram-bot/src/api.py`, `telegram-bot/src/services/stream_listener.py`, `telegram-bot/src/keyboards.py`
