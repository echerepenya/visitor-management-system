# System Settings Table

Статус: done

## Рішення
Створено нову модель `SystemSettings` (замість `ParkingSettings`), що містить глобальні конфігурації системи (наприклад, `guest_parking_spots`, `guest_parking_post_id`). В SQLAdmin додано кастомну сторінку `SettingsView` для керування цими налаштуваннями.

## Чому
Жорстке кодування (hardcode) налаштувань, таких як кількість паркомісць і пост охорони, якому надсилаються повідомлення, не дозволяє гнучко керувати системою. Замість окремої моделі для парковки вирішено зробити єдину модель `SystemSettings`, щоб у майбутньому можна було додавати інші глобальні налаштування. Кастомна сторінка `SettingsView` дозволяє зручно групувати налаштування в адмін-панелі.

## Зачеплені файли/модулі
- `src/models/system_settings.py` (нова)
- `src/models/parking.py`
- `src/services/parking.py`
- `src/admin/settings_admin.py` (нова)
- `templates/sqladmin/settings.html` (нова)
- `src/routers/telegram.py`
