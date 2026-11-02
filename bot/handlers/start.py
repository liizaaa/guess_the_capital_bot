from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.keyboards.main import main_menu_keyboard
from database.user_service import get_or_create_user
from database.database import async_session
from database.models import User, UserAchievement, Achievement, Game

router = Router()


# Главное меню при запуске бота
@router.message(CommandStart())
async def start_handler(message: Message):
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    await message.answer(
        "👋 <b>Добро пожаловать в «Угадай столицу»!</b>\n\n"
        "🌍 Проверь свои знания географии.\n"
        "⏱ На каждый вопрос у тебя будет 30 секунд.\n\n"
        f"👤 Игрок: <b>{user.first_name or 'Игрок'}</b>\n"
        f"⭐ Уровень: <b>{user.level}</b>\n"
        f"✨ XP: <b>{user.xp}</b>\n\n"
        "Готов проверить себя?",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )

# Открытие настроек через команду /settings
@router.message(Command("settings"))
async def settings_command(message: Message, state: FSMContext):
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    data = await state.get_data()
    hints_enabled = data.get("hints_enabled", True)

    hints_status = "✅ Включены" if hints_enabled else "❌ Выключены"
    notifications_status = (
        "✅ Включены"
        if user.notifications_enabled
        else "❌ Выключены"
    )

    notification_button = (
        "🔕 Отключить уведомления"
        if user.notifications_enabled
        else "🔔 Включить уведомления"
    )

    text = (
        "⚙️ <b>Настройки игры</b>\n\n"
        f"💡 Подсказки: {hints_status}\n"
        f"🔔 Уведомления: {notifications_status}\n\n"
        "Настрой игру под себя!"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💡 Вкл./выкл. подсказки",
                    callback_data="toggle_hints",
                )
            ],
            [
                InlineKeyboardButton(
                    text=notification_button,
                    callback_data="toggle_notifications",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="main_menu",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Сбросить прогресс",
                    callback_data="reset_progress",
                )
            ],
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

# Профиль игрока
@router.callback_query(F.data == "profile")
async def profile_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )

    if user.games_played > 0:
        accuracy = user.correct_answers / user.games_played * 100
    else:
        accuracy = 0

    name = user.first_name or user.username or "Игрок"

    # Получаем достижения пользователя
    async with async_session() as session:
        result = await session.execute(
            select(Achievement)
            .join(
                UserAchievement,
                UserAchievement.achievement_id == Achievement.id
            )
            .where(UserAchievement.user_id == user.id)
            .order_by(UserAchievement.earned_at)
        )
        achievements = result.scalars().all()

    if achievements:
        achievements_text = "\n\n🏆 <b>Мои достижения</b>\n\n"

        for achievement in achievements:
            achievements_text += (
                f"🎖 <b>{achievement.name}</b>\n"
                f"📌 {achievement.description}\n"
                f"✨ Награда: {achievement.xp_reward} XP\n\n"
            )
    else:
        achievements_text = (
            "\n\n🏆 <b>Мои достижения</b>\n"
            "Пока достижений нет. Продолжай играть! 🌍"
        )

    text = (
        f"👤 <b>Профиль игрока</b>\n\n"
        f"Привет, {name}!\n\n"
        f"⭐ Уровень: <b>{user.level}</b>\n"
        f"✨ Опыт: <b>{user.xp} XP</b>\n\n"
        f"🎮 Сыграно вопросов: <b>{user.games_played}</b>\n"
        f"✅ Правильных ответов: <b>{user.correct_answers}</b>\n"
        f"🎯 Точность ответов: <b>{accuracy:.1f}%</b>\n"
        f"🔥 Лучший стрик: <b>{user.best_streak}</b>"
        f"{achievements_text}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# Таблица лидеров
@router.callback_query(F.data == "leaderboard")
async def leaderboard_handler(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .order_by(User.xp.desc(), User.level.desc())
            .limit(10)
        )
        users = result.scalars().all()

    if not users:
        text = (
            "🏆 <b>Таблица лидеров</b>\n\n"
            "Пока игроков нет. Стань первым!"
        )
    else:
        medals = ["🥇", "🥈", "🥉"]
        lines = ["🏆 <b>ТОП-10 игроков</b>\n"]

        for position, user in enumerate(users, start=1):
            medal = (
                medals[position - 1]
                if position <= 3
                else f"{position}."
            )
            name = user.first_name or user.username or "Игрок"

            lines.append(
                f"{medal} <b>{name}</b>\n"
                f"   ⭐ Уровень: {user.level} | "
                f"✨ Опыт: {user.xp} XP"
            )

        text = "\n\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# Меню настроек
@router.callback_query(F.data == "settings")
async def settings_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
    )

    data = await state.get_data()
    hints_enabled = data.get("hints_enabled", True)

    hints_status = "✅ Включены" if hints_enabled else "❌ Выключены"
    notifications_status = (
        "✅ Включены"
        if user.notifications_enabled
        else "❌ Выключены"
    )

    notification_button = (
        "🔕 Отключить уведомления"
        if user.notifications_enabled
        else "🔔 Включить уведомления"
    )

    text = (
        "⚙️ <b>Настройки игры</b>\n\n"
        f"💡 Подсказки: {hints_status}\n"
        f"🔔 Уведомления: {notifications_status}\n\n"
        "Настрой игру под себя!"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💡 Вкл./выкл. подсказки",
                    callback_data="toggle_hints",
                )
            ],
            [
                InlineKeyboardButton(
                    text=notification_button,
                    callback_data="toggle_notifications",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="main_menu",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Сбросить прогресс",
                    callback_data="reset_progress",
                )
            ],
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


# Включение и выключение подсказок
@router.callback_query(F.data == "toggle_hints")
async def toggle_hints_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    data = await state.get_data()
    hints_enabled = data.get("hints_enabled", True)

    await state.update_data(
        hints_enabled=not hints_enabled
    )

    await settings_handler(callback, state)


# Включение и выключение уведомлений через базу данных
@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "Пользователь не найден. Отправь /start.",
                show_alert=True,
            )
            return

        user.notifications_enabled = not user.notifications_enabled
        await session.commit()

    await settings_handler(callback, state)

# Подтверждение сброса прогресса
@router.callback_query(F.data == "reset_progress")
async def reset_progress_handler(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, сбросить",
                    callback_data="confirm_reset",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="settings",
                ),
            ]
        ]
    )

    await callback.message.edit_text(
        "⚠️ <b>Сброс прогресса</b>\n\n"
        "Ты действительно хочешь начать заново?\n\n"
        "Будут удалены:\n"
        "• Статистика ответов\n"
        "• Опыт и уровень\n"
        "• Серии правильных ответов\n"
        "• История игр\n"
        "• Полученные достижения\n\n"
        "Это действие нельзя отменить!",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


# Выполнение сброса прогресса
@router.callback_query(F.data == "confirm_reset")
async def confirm_reset_handler(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == callback.from_user.id
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            await callback.answer(
                "Пользователь не найден.",
                show_alert=True,
            )
            return

        # Удаляем историю игр
        await session.execute(
            Game.__table__.delete().where(
                Game.user_id == user.id
            )
        )

        # Удаляем достижения пользователя
        await session.execute(
            UserAchievement.__table__.delete().where(
                UserAchievement.user_id == user.id
            )
        )

        # Обнуляем статистику
        user.xp = 0
        user.level = 1
        user.games_played = 0
        user.correct_answers = 0
        user.streak = 0
        user.best_streak = 0

        await session.commit()

    await callback.message.edit_text(
        "✅ <b>Прогресс успешно сброшен!</b>\n\n"
        "Теперь ты можешь начать игру заново. 🌍",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()