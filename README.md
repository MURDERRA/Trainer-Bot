# 🏋️ Workout Bot

Telegram-бот для персональных тренировок с автоматическим расписанием и трекингом прогресса.

## ✨ Основные возможности

- **3 тренировки в день** с разным фокусом:
  - 🌅 **Утро (11:00)** — верх тела (грудь, трицепс, плечи)
  - ☀️ **День (16:00)** — ноги + кор
  - 🌙 **Вечер (22:30)** — полное тело, лёгкая нагрузка

- **Рандизация упражнений** — 3 варианта на каждый слот, не надоест

- **Трекинг выполнения**:
  - ✅ Подтверждение прочтения уведомления
  - ⬜ Отметка выполненных упражнений
  - 💧 Напоминание выпить воды

- **Автонапоминания** — каждые 10 минут пока не подтвердишь

- **Команды управления**:
  - `/start` — приветствие и расписание
  - `/status` — статус сегодняшних сессий
  - `/test` — тестовое уведомление
  - `/morning`, `/afternoon`, `/evening` — запуск конкретной сессии

## 🛠 Технологический стек

| Компонент     | Технология           |
| ------------- | -------------------- |
| Язык          | Python 3             |
| Framework     | aiogram 3 (async)    |
| Планировщик   | APScheduler          |
| Развёртывание | systemd user service |
| OS            | Arch Linux           |

## 🚀 Быстрый старт

```bash
# 1. Создай бота в @BotFather и получи токен
# 2. Узнай свой user ID через @userinfobot

# 3. Установка
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Настройка
cp .env.example .env
# Отредактируй .env — вставь BOT_TOKEN и USER_ID

# 5. Запуск
python bot.py
```

## 📁 Структура проекта

```
Trainer-Bot/
├── bot.py              # Основной код бота
├── requirements.txt    # Зависимости
├── .env.example        # Шаблон переменных окружения
├── workout-bot.service # systemd unit для автозапуска
└── README.md           # Документация
```

## 📅 Расписание по умолчанию

| Время | Слот      | Длительность |
| ----- | --------- | ------------ |
| 11:00 | morning   | 5–7 мин      |
| 16:00 | afternoon | 5–7 мин      |
| 22:30 | evening   | 5–7 мин      |

> ⚙️ Timezone: `Europe/Moscow` (изменить в `bot.py` — `AsyncIOScheduler(timezone="...")`)

## 🔧 Автозапуск через systemd

```bash
# Создай директорию для user service
mkdir -p ~/.config/systemd/user

# Скопируй unit-файл
cp workout-bot.service ~/.config/systemd/user/

# Перезагрузи daemon и включи сервис
systemctl --user daemon-reload
systemctl --user enable workout-bot.service
systemctl --user start workout-bot.service

# Проверка статуса
systemctl --user status workout-bot.service

# Просмотр логов
journalctl --user -u workout-bot.service -f
```
