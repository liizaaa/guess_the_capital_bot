from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Начать игру",
                    callback_data="start_game"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 Профиль",
                    callback_data="profile"
                ),
                InlineKeyboardButton(
                    text="🏆 Лидеры",
                    callback_data="leaderboard"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="settings"
                )
            ],
        ]
    )