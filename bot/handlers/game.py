import asyncio
import time

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery

from bot.keyboards.game import (
    answer_keyboard,
    next_question_keyboard,
)
from bot.states.game_states import GameStates
from bot.services.quiz_service import generate_question
from bot.services.maps_service import get_capital_map
from database.game_service import save_game_result
from bot.keyboards.main import main_menu_keyboard

router = Router()


async def cancel_timer(state: FSMContext):
    """Отменяет текущий таймер вопроса."""

    data = await state.get_data()
    timer_task = data.get("timer_task")

    if timer_task and not timer_task.done():
        timer_task.cancel()

        try:
            await timer_task
        except asyncio.CancelledError:
            pass

    await state.update_data(timer_task=None)


async def question_timer(message, state):
    """Ожидает 30 секунд и завершает вопрос по тайм-ауту."""

    try:
        await asyncio.sleep(30)

        if (
            await state.get_state()
            != GameStates.waiting_for_answer.state
        ):
            return

        data = await state.get_data()

        await save_game_result(
            telegram_id=message.chat.id,
            country=data["country"],
            correct_capital=data["correct_capital"],
            user_answer=None,
            is_correct=False,
            time_spent=30.0,
            hints_used=data.get("hints_used", 0),
        )

        await message.edit_text(
            "⏰ <b>Время вышло!</b>\n\n"
            f"Правильный ответ: "
            f"<b>{data['correct_capital']}</b>\n\n"
            "Попробуй следующий вопрос! 🌍",
            reply_markup=next_question_keyboard(),
            parse_mode="HTML",
        )

        hints_enabled = data.get("hints_enabled", True)

        await state.clear()
        await state.update_data(
            hints_enabled=hints_enabled
        )

    except asyncio.CancelledError:
        return


async def send_question(callback, state):
    """Показывает новый вопрос и запускает таймер."""

    await cancel_timer(state)
    data = await state.get_data()
    hints_enabled = data.get("hints_enabled", True)

    question = await generate_question()

    if question is None:
        await callback.answer(
            "Не удалось получить данные для игры.",
            show_alert=True,
        )
        return

    await state.update_data(
        country=question["country"],
        correct_capital=question["capital"],
        options=question["options"],
        started_at=time.monotonic(),
        hints_used=0,
        first_letter_hint_used=False,
        map_hint_used=False,
        timer_task=None,
        hints_enabled=hints_enabled,
    )

    await state.set_state(
        GameStates.waiting_for_answer
    )

    data = await state.get_data()
    hints_enabled = data.get("hints_enabled", True)

    await callback.message.edit_text(
        f"🌍 <b>Вопрос</b>\n\n"
        f"Какая столица у страны:\n\n"
        f"<b>{question['flag']} "
        f"{question['country']}</b>\n\n"
        "⏱ У тебя есть <b>30 секунд</b>!",
        reply_markup=answer_keyboard(
            question["options"],
            show_hint=hints_enabled,
            show_map_hint=hints_enabled,
        ),
        parse_mode="HTML",
    )

    await callback.answer()

    timer_task = asyncio.create_task(
        question_timer(callback.message, state)
    )

    await state.update_data(
        timer_task=timer_task
    )


@router.callback_query(F.data == "start_game")
async def start_game(callback, state):
    await send_question(callback, state)


@router.callback_query(
    GameStates.waiting_for_answer,
    F.data == "hint:first_letter",
)
async def first_letter_hint(callback, state):
    """Показывает первую букву столицы."""

    data = await state.get_data()

    if not data.get("hints_enabled", True):
        await callback.answer(
            "Подсказки отключены в настройках!",
            show_alert=True,
        )
        return

    if data.get("first_letter_hint_used", False):
        await callback.answer(
            "💡 Ты уже использовал эту подсказку.",
            show_alert=True,
        )
        return

    if time.monotonic() - data["started_at"] >= 30:
        await callback.answer(
            "⏰ Время уже вышло!",
            show_alert=True,
        )
        return

    capital = data["correct_capital"].strip()

    if not capital:
        await callback.answer(
            "Не удалось получить подсказку.",
            show_alert=True,
        )
        return

    await state.update_data(
        first_letter_hint_used=True,
        hints_used=1 + int(data.get("map_hint_used", False)),
    )

    await callback.message.edit_reply_markup(
        reply_markup=answer_keyboard(
            data["options"],
            show_hint=False,
            show_map_hint=not data.get("map_hint_used", False),
        )
    )

    await callback.answer(
        f"💡 Столица начинается на букву «{capital[0].upper()}»",
        show_alert=True,
    )


@router.callback_query(
    GameStates.waiting_for_answer,
    F.data == "hint:map",
)
async def map_hint(callback, state):
    """Отправляет карту отдельным сообщением."""

    data = await state.get_data()

    if not data.get("hints_enabled", True):
        await callback.answer(
            "Подсказки отключены в настройках!",
            show_alert=True,
        )
        return

    if data.get("map_hint_used", False):
        await callback.answer(
            "🗺️ Ты уже использовал эту подсказку.",
            show_alert=True,
        )
        return

    if time.monotonic() - data["started_at"] >= 30:
        await callback.answer(
            "⏰ Время уже вышло!",
            show_alert=True,
        )
        return

    # Сначала получаем карту.
    # Пока запрос выполняется, таймер продолжает идти.
    await callback.answer("🗺️ Загружаю карту...")

    image = await get_capital_map(
        capital=data["correct_capital"],
        country=data["country"],
    )

    # Проверяем, не закончился ли вопрос во время запроса.
    current_data = await state.get_data()

    if (
        await state.get_state()
        != GameStates.waiting_for_answer.state
    ):
        return

    if time.monotonic() - current_data["started_at"] >= 30:
        return

    if image is None:
        await callback.message.answer(
            "Не удалось загрузить карту. "
            "Попробуй продолжить без неё."
        )
        return

    # Отправляем карту отдельным сообщением.
    await callback.message.answer_photo(
        photo=BufferedInputFile(
            image,
            filename="capital_map.png",
        ),
        caption=(
            f"🗺️ Карта для вопроса: "
            f"{data['country']}"
        ),
    )

    # Сохраняем использование подсказки только после успеха.
    await state.update_data(
        map_hint_used=True,
        hints_used=1 + int(
            current_data.get("first_letter_hint_used", False)
        ),
    )

    # Убираем только кнопку карты.
    await callback.message.edit_reply_markup(
        reply_markup=answer_keyboard(
            data["options"],
            show_hint=not current_data.get(
                "first_letter_hint_used", False
            ),
            show_map_hint=False,
        )
    )


@router.callback_query(
    GameStates.waiting_for_answer,
    F.data.startswith("answer:"),
)
async def answer_question(callback, state):
    """Обрабатывает ответ и начисляет XP."""

    data = await state.get_data()

    elapsed_time = time.monotonic() - data["started_at"]

    if elapsed_time >= 30:
        await callback.answer(
            "⏰ Время уже вышло!",
            show_alert=True,
        )
        return

    await cancel_timer(state)

    user_answer = callback.data.split(":", 1)[1]
    correct_answer = data["correct_capital"]

    is_correct = user_answer == correct_answer

    if is_correct:
        result = "✅ <b>Правильно!</b>"
    else:
        result = (
            "❌ <b>Неправильно!</b>\n"
            f"Правильный ответ: <b>{correct_answer}</b>"
        )

    hints_used = data.get("hints_used", 0)

    user = await save_game_result(
        telegram_id=callback.from_user.id,
        country=data["country"],
        correct_capital=correct_answer,
        user_answer=user_answer,
        is_correct=is_correct,
        time_spent=elapsed_time,
        hints_used=hints_used,
    )

    xp = 0

    if is_correct:
        if hints_used == 0:
            xp = 10
        elif hints_used == 1:
            xp = 7
        else:
            xp = 5

    if user:
        profile_info = (
            f"\n\n⭐ Уровень: <b>{user.level}</b>"
            f"\n✨ Всего XP: <b>{user.xp}</b>"
        )

        achievements_text = ""

        for achievement in getattr(user, "new_achievements", []):
            achievements_text += (
                "\n\n🏆 <b>Новое достижение!</b>\n"
                f"🎖 {achievement['name']}\n"
                f"📌 {achievement['description']}\n"
                f"✨ Награда: +{achievement['xp_reward']} XP"
            )
    else:
        profile_info = ""
        achievements_text = ""

    await callback.message.edit_text(
        f"{result}\n\n"
        f"⏱ Время: <b>{elapsed_time:.1f} сек.</b>\n"
        f"✨ XP за ответ: <b>+{xp}</b>"
        f"{profile_info}"
        f"{achievements_text}\n\n"
        "Готов к следующему вопросу? 🌍",
        reply_markup=next_question_keyboard(),
        parse_mode="HTML",
    )

    data = await state.get_data()
    hints_enabled = data.get("hints_enabled", True)

    await state.clear()
    await state.update_data(
        hints_enabled=hints_enabled
    )

    await callback.answer()


@router.callback_query(F.data == "next_question")
async def next_question(callback, state):
    await send_question(callback, state)

@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
):
    # Сохраняем настройку подсказок
    data = await state.get_data()
    hints_enabled = data.get("hints_enabled", True)

    # Отменяем таймер
    await cancel_timer(state)

    # Очищаем состояние игры
    await state.clear()

    # Возвращаем настройку подсказок
    await state.update_data(
        hints_enabled=hints_enabled
    )

    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\n"
        "Выбери, что хочешь сделать:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()