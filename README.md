# 🏋️ Workout Bot — Setup на Arch Linux

## 1. Создай бота

1. Открой Telegram → @BotFather → `/newbot`
2. Сохрани токен
3. Узнай свой user ID через @userinfobot

---

## 2. Установи зависимости

```fish
# Создай venv (один раз)
mkdir -p ~/.local/share/workout_bot
python -m venv ~/.local/share/workout_bot/venv

# Установи пакеты
~/.local/share/workout_bot/venv/bin/pip install aiogram apscheduler python-dotenv
```

---

## 3. Разложи файлы

```fish
mkdir -p ~/.config/workout_bot
cp bot.py ~/.config/workout_bot/
cp .env ~/.config/workout_bot/
```

Отредактируй `.env`:
```fish
nvim ~/.config/workout_bot/.env
```

Вставь свой токен и user_id.

---

## 4. Проверь вручную

```fish
~/.local/share/workout_bot/venv/bin/python ~/.config/workout_bot/bot.py
```

Напиши боту `/start` — должен ответить. `/test` — пришлёт тестовую зарядку.

---

## 5. Автозапуск через systemd user service

```fish
mkdir -p ~/.config/systemd/user
cp workout-bot.service ~/.config/systemd/user/

systemctl --user daemon-reload
systemctl --user enable workout-bot.service
systemctl --user start workout-bot.service

# Проверить статус
systemctl --user status workout-bot.service

# Логи
journalctl --user -u workout-bot.service -f
```

---

## 6. Команды бота

| Команда      | Что делает                        |
| ------------ | --------------------------------- |
| `/start`     | Приветствие и расписание          |
| `/status`    | Статус сегодняшних сессий         |
| `/test`      | Тестовое уведомление прямо сейчас |
| `/morning`   | Запустить утреннюю сессию         |
| `/afternoon` | Запустить дневную сессию          |
| `/evening`   | Запустить вечернюю сессию         |

---

## Расписание

| Время | Слот      | Фокус                             |
| ----- | --------- | --------------------------------- |
| 11:00 | morning   | Верх тела (грудь, трицепс, плечи) |
| 16:00 | afternoon | Ноги + кор                        |
| 22:30 | evening   | Полное тело, лёгкая нагрузка      |

Каждый слот имеет **3 случайных варианта** упражнений — не надоест!

---

## Timezone

По умолчанию стоит `Europe/Moscow`. Если нужно другое — измени в `bot.py`:

```python
scheduler = AsyncIOScheduler(timezone="Europe/Berlin")
```