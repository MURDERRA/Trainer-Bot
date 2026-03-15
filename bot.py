#!/usr/bin/env python3
"""
Workout reminder Telegram bot.
Schedules 3 daily sessions (11:00, 16:00, 22:30),
tracks read confirmations and exercise completion.
"""

import asyncio
import json
import logging
import os
import random
from datetime import datetime, time
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
USER_ID: int = int(os.environ["USER_ID"])

# ---------------------------------------------------------------------------
# Workout content
# ---------------------------------------------------------------------------

WARMUP = [
    "🔄 Повороты головы влево/вправо — 10 раз",
    "🔄 Круги плечами вперёд и назад — 10 раз",
    "🙌 Махи руками (мельница) — 15 раз",
    "🌀 Круговые движения тазом — 10 раз",
    "🦵 Подъём колен на месте — 20 раз",
]

# Each session slot has its own muscle focus pools
WORKOUTS: dict[str, list[list[dict]]] = {
    "morning": [  # 11:00 — верх тела
        [
            {
                "name":
                "💪 Отжимания стандарт — ладони чуть шире плеч, грудь касается пола",
                "reps": "3×10"
            },
            {
                "name":
                "🔝 Подтягивания широким хватом (или австралийские если тяжело)",
                "reps": "3×5-8"
            },
            {
                "name":
                "🦾 Отжимания узким хватом (трицепс) — локти прижаты к телу",
                "reps": "3×8"
            },
            {
                "name": "Планка на прямых руках — тело прямое как доска",
                "reps": "3×30 сек"
            },
            {
                "name":
                "🙆 Растяжка грудных: встань в дверной проём, упрись руками, наклонись вперёд",
                "reps": "30 сек"
            },
        ],
        [
            {
                "name": "🤸 Отжимания широким хватом (акцент на грудь) ",
                "reps": "3×10"
            },
            {
                "name":
                "🔝 Подтягивания обратным хватом (бицепс) — ладони к себе",
                "reps": "3×5-8"
            },
            {
                "name":
                "💪 Алмазные отжимания — большие и указательные пальцы образуют ромб",
                "reps": "3×8"
            },
            {
                "name":
                "🧘 Боковая планка — держи бёдра на весу, не проваливайся",
                "reps": "2×20 сек каждая сторона"
            },
            {
                "name":
                "🙆 Растяжка плеч: одну руку прижми к груди другой рукой, держи",
                "reps": "30 сек каждая"
            },
        ],
        [
            {
                "name":
                "💪 Отжимания с паузой — опустись и задержись 2 сек внизу",
                "reps": "3×8"
            },
            {
                "name": "🔝 Вис на турнике — просто виси, расслабив спину",
                "reps": "3×20-30 сек"
            },
            {
                "name":
                "🤸 Отжимания пайк — таз поднят вверх, тело домиком, качаешь плечи",
                "reps": "3×8"
            },
            {
                "name":
                "🧘 Планка с касанием плеч — поочерёдно касайся плеча противоположной рукой",
                "reps": "2×10 раз"
            },
            {
                "name":
                "🙆 Растяжка спины на турнике: повисни и медленно поворачивай корпус влево-вправо",
                "reps": "30 сек"
            },
        ],
    ],
    "afternoon": [  # 16:00 — ноги + кор
        [
            {
                "name":
                "🦵 Приседания классика — стопы чуть шире плеч, колени не заваливай внутрь",
                "reps": "3×15"
            },
            {
                "name":
                "🦵 Выпады вперёд — шаг вперёд, заднее колено почти касается пола",
                "reps": "3×10 каждая нога"
            },
            {
                "name":
                "🍑 Ягодичный мост — лёжа на спине, ступни у ягодиц, толкай таз вверх",
                "reps": "3×15"
            },
            {
                "name":
                "💪 Скручивания — лёжа, руки за головой, поднимай только лопатки",
                "reps": "3×15"
            },
            {
                "name":
                "🙆 Растяжка задней поверхности бедра: сядь на пол, вытяни ногу, тянись руками к стопе",
                "reps": "30 сек каждая"
            },
        ],
        [
            {
                "name":
                "🦵 Приседания с паузой — опустись и задержись 2 сек внизу",
                "reps": "3×12"
            },
            {
                "name":
                "🦵 Боковые выпады — шаг в сторону, присядь на одну ногу, другая прямая",
                "reps": "3×10 каждая"
            },
            {
                "name":
                "🍑 Ягодичный мост на одной ноге — одна нога вытянута, толкай таз",
                "reps": "2×10 каждая"
            },
            {
                "name":
                "💪 Велосипед — лёжа, поочерёдно тяни локоть к противоположному колену",
                "reps": "3×20"
            },
            {
                "name":
                "🙆 Растяжка паха: сядь, сведи ступни вместе, надавливай локтями на колени",
                "reps": "30 сек"
            },
        ],
        [
            {
                "name":
                "🦵 Плие — широкие стопы, носки развёрнуты в стороны, приседай",
                "reps": "3×15"
            },
            {
                "name":
                "🦵 Реверсивные выпады — шаг назад, заднее колено почти касается пола",
                "reps": "3×10 каждая"
            },
            {
                "name":
                "🍑 Ягодичный мост с задержкой — поднялся, сожми ягодицы, держи 2 сек",
                "reps": "3×12"
            },
            {
                "name":
                "💪 Планка с подъёмом ног — на локтях, поочерёдно поднимай прямую ногу",
                "reps": "3×10 каждая"
            },
            {
                "name":
                "🙆 Растяжка поясницы: лёжа на спине, подтяни оба колена к груди, покачайся",
                "reps": "30-45 сек"
            },
        ],
    ],
    "evening": [  # 22:30 — полное тело лёгко + расслабление
        [
            {
                "name":
                "🤸 Берпи медленные — присел, выпрыгнул ногами назад в упор лёжа, встал ",
                "reps": "3×5"
            },
            {
                "name": "💪 Отжимания — в спокойном темпе",
                "reps": "2×8"
            },
            {
                "name": "🦵 Приседания — не торопись",
                "reps": "2×12"
            },
            {
                "name":
                "🔝 Вис на турнике с раскачкой — виси, медленно раскачивайся, вытягивай позвоночник",
                "reps": "2×20 сек"
            },
            {
                "name":
                "🙆 Наклон вперёд стоя — ноги прямые, тянись руками к полу, расслабь шею",
                "reps": "30 сек"
            },
        ],
        [
            {
                "name":
                "🌀 Суставная разминка — по 10 кругов каждым суставом от шеи до голеностопа",
                "reps": "1 мин"
            },
            {
                "name": "🦵 Медленные приседания — 4 сек вниз, 2 сек вверх",
                "reps": "2×10"
            },
            {
                "name":
                "💪 Отжимания от стула/дивана (облегчённые) — руки на возвышении",
                "reps": "2×10"
            },
            {
                "name": "🔝 Вис на турнике — просто расслабленно виси, дыши",
                "reps": "2×25 сек"
            },
            {
                "name":
                "🙆 Растяжка грудного отдела: сядь на стул, руки за голову, прогнись назад через спинку",
                "reps": "по 30 сек"
            },
        ],
        [
            {
                "name":
                "🤸 Прыжки на месте — ноги вместе/врозь или просто подпрыгивай",
                "reps": "2×20"
            },
            {
                "name":
                "🦵 Выпады с поворотом — делаешь выпад вперёд и поворачиваешь корпус в сторону передней ноги",
                "reps": "2×8 каждая"
            },
            {
                "name": "💪 Планка на локтях — держись, не проваливай поясницу",
                "reps": "2×30 сек"
            },
            {
                "name":
                "🔝 Вис на турнике + подтягивание лопаток — виси и поднимай лопатки без сгибания рук",
                "reps": "2×10"
            },
            {
                "name":
                "🙆 Растяжка подколенных сухожилий: лёжа на спине, подними прямую ногу и тяни к себе",
                "reps": "30 сек каждая"
            },
        ],
    ],
}

SLOT_LABELS = {
    "morning": "🌅 Утренняя зарядка (11:00)",
    "afternoon": "☀️ Дневная зарядка (16:00)",
    "evening": "🌙 Вечерняя зарядка (22:30)",
}

# ---------------------------------------------------------------------------
# In-memory state  (per session message)
# ---------------------------------------------------------------------------
# sessions[session_key] = {
#   "read_msg_id": int,
#   "workout_msg_id": int,
#   "read": bool,
#   "exercises": {index: bool},
#   "reminder_task": asyncio.Task | None,
# }
sessions: dict[str, dict] = {}


def session_key(slot: str, date: str) -> str:
    return f"{slot}:{date}"


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Keyboard builders
# ---------------------------------------------------------------------------


def read_keyboard(key: str, confirmed: bool) -> InlineKeyboardMarkup:
    if confirmed:
        btn = InlineKeyboardButton(text="✅ Прочитал!",
                                   callback_data=f"read:{key}")
    else:
        btn = InlineKeyboardButton(text="👀 Прочитал!",
                                   callback_data=f"read:{key}")
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])


def workout_keyboard(key: str, exercises: list[dict],
                     done: dict[int, bool]) -> InlineKeyboardMarkup:
    rows = []
    for i, ex in enumerate(exercises):
        check = "✅ " if done.get(i) else "⬜ "
        btn = InlineKeyboardButton(
            text=f"{check}{ex['name']} — {ex['reps']}",
            callback_data=f"ex:{key}:{i}",
        )
        rows.append([btn])
    # water reminder button
    water_done = done.get(-1, False)
    water_btn = InlineKeyboardButton(
        text=("✅ " if water_done else "🚰 ") + "Выпил стакан воды",
        callback_data=f"ex:{key}:-1",
    )
    rows.append([water_btn])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------------------------------------------------------------------
# Core send logic
# ---------------------------------------------------------------------------


async def send_session(bot: Bot, slot: str):
    date = today()
    key = session_key(slot, date)

    # Pick random workout variant for this slot
    variant = random.choice(WORKOUTS[slot])
    warmup_pick = random.sample(WARMUP, 3)

    text = (f"{SLOT_LABELS[slot]}\n\n"
            f"⏱ 5–7 минут, интенсивность ~70%\n\n"
            f"**Разминка (1 мин):**\n" + "\n".join(f"  • {w}"
                                                   for w in warmup_pick) +
            "\n\n**Блок нагрузки (3–4 мин):**\n" +
            "\n".join(f"  • {e['name']} — {e['reps']}"
                      for e in variant[:3]) + "\n\n**Растяжка (1–2 мин):**\n" +
            "\n".join(f"  • {e['name']} — {e['reps']}" for e in variant[3:]) +
            "\n\n🚰 После зарядки — выпей стакан воды (комнатная температура)!")

    # Send read-confirmation message
    read_msg = await bot.send_message(
        USER_ID,
        f"🔔 *{SLOT_LABELS[slot]}* — пора размяться!\n\nНажми кнопку, когда прочитал задание 👇",
        parse_mode="Markdown",
        reply_markup=read_keyboard(key, False),
    )

    # Send workout detail message
    workout_msg = await bot.send_message(
        USER_ID,
        text,
        parse_mode="Markdown",
        reply_markup=workout_keyboard(key, variant, {}),
    )

    sessions[key] = {
        "slot": slot,
        "read_msg_id": read_msg.message_id,
        "workout_msg_id": workout_msg.message_id,
        "read": False,
        "exercises": variant,
        "done": {},
        "reminder_task": None,
    }

    # Start repeat reminder every 10 min if not read
    # task = asyncio.create_task(repeat_reminder(bot, key))
    # sessions[key]["reminder_task"] = task


async def repeat_reminder(bot: Bot, key: str):
    """Resend read-prompt every 10 minutes until confirmed."""
    await asyncio.sleep(600)
    while True:
        s = sessions.get(key)
        if not s or s["read"]:
            return
        try:
            await bot.send_message(
                USER_ID,
                f"⏰ Напоминание! Ты ещё не отметил, что прочитал зарядку.\n"
                f"Нажми кнопку выше или /status чтобы проверить.",
            )
        except Exception as e:
            log.warning("reminder send failed: %s", e)
        await asyncio.sleep(600)


# ---------------------------------------------------------------------------
# Callback handlers
# ---------------------------------------------------------------------------


async def handle_read(callback: CallbackQuery, key: str, bot: Bot):
    s = sessions.get(key)
    if not s:
        await callback.answer("Сессия устарела.")
        return

    s["read"] = True
    if s["reminder_task"]:
        s["reminder_task"].cancel()

    try:
        await bot.edit_message_reply_markup(
            chat_id=USER_ID,
            message_id=s["read_msg_id"],
            reply_markup=read_keyboard(key, confirmed=True),
        )
    except Exception:
        pass

    await callback.answer("✅ Отмечено! Удачи с зарядкой 💪")


async def handle_exercise(callback: CallbackQuery, key: str, ex_index: int,
                          bot: Bot):
    s = sessions.get(key)
    if not s:
        await callback.answer("Сессия устарела.")
        return

    # Toggle
    s["done"][ex_index] = not s["done"].get(ex_index, False)
    state = s["done"][ex_index]

    try:
        await bot.edit_message_reply_markup(
            chat_id=USER_ID,
            message_id=s["workout_msg_id"],
            reply_markup=workout_keyboard(key, s["exercises"], s["done"]),
        )
    except Exception:
        pass

    if ex_index == -1:
        await callback.answer("💧 Вода отмечена!" if state else "↩️ Снято")
    else:
        name = s["exercises"][ex_index]["name"]
        await callback.answer(("✅ Сделано: " if state else "↩️ Снято: ") +
                              name)


# ---------------------------------------------------------------------------
# Dispatcher setup
# ---------------------------------------------------------------------------


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: Message):
        await message.answer(
            "👋 Привет! Я буду напоминать тебе делать зарядку 3 раза в день:\n"
            "🌅 11:00 — утренняя (верх тела)\n"
            "☀️ 16:00 — дневная (ноги + кор)\n"
            "🌙 22:30 — вечерняя (полное тело, лёгко)\n\n"
            "Команды:\n"
            "/status — статус сегодняшних сессий\n"
            "/test — отправить тестовое уведомление прямо сейчас\n"
            "/morning /afternoon /evening — запустить конкретную сессию")

    @dp.message(Command("status"))
    async def cmd_status(message: Message):
        date = today()
        lines = [f"📊 Статус на {date}:"]
        for slot in ("morning", "afternoon", "evening"):
            key = session_key(slot, date)
            s = sessions.get(key)
            if not s:
                lines.append(f"  {SLOT_LABELS[slot]}: ⏳ ещё не было")
            else:
                read_mark = "✅" if s["read"] else "❌"
                total = len(s["exercises"]) + 1  # +water
                done_count = sum(1 for v in s["done"].values() if v)
                lines.append(
                    f"  {SLOT_LABELS[slot]}: прочитал {read_mark} | упражнений {done_count}/{total}"
                )
        await message.answer("\n".join(lines))

    @dp.message(Command("test"))
    async def cmd_test(message: Message):
        bot: Bot = message.bot
        # pick random slot for test
        slot = random.choice(["morning", "afternoon", "evening"])
        await send_session(bot, slot)
        await message.answer(
            f"✅ Тестовое уведомление отправлено ({SLOT_LABELS[slot]})")

    @dp.message(Command("morning"))
    async def cmd_morning(message: Message):
        await send_session(message.bot, "morning")

    @dp.message(Command("afternoon"))
    async def cmd_afternoon(message: Message):
        await send_session(message.bot, "afternoon")

    @dp.message(Command("evening"))
    async def cmd_evening(message: Message):
        await send_session(message.bot, "evening")

    @dp.callback_query(F.data.startswith("read:"))
    async def cb_read(callback: CallbackQuery):
        key = callback.data.split(":", 1)[1]
        await handle_read(callback, key, callback.bot)

    @dp.callback_query(F.data.startswith("ex:"))
    async def cb_exercise(callback: CallbackQuery):
        parts = callback.data.split(":")
        key = f"{parts[1]}:{parts[2]}"
        ex_index = int(parts[3])
        await handle_exercise(callback, key, ex_index, callback.bot)

    return dp


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = build_dispatcher()

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_session,
                      "cron",
                      hour=11,
                      minute=0,
                      args=[bot, "morning"])
    scheduler.add_job(send_session,
                      "cron",
                      hour=16,
                      minute=0,
                      args=[bot, "afternoon"])
    scheduler.add_job(send_session,
                      "cron",
                      hour=22,
                      minute=30,
                      args=[bot, "evening"])
    scheduler.start()

    log.info("Bot started. Waiting for events...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
