from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def answer_keyboard(
    options: list[str],
    show_hint: bool = True,
    show_map_hint: bool = True,
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=option,
                callback_data=f"answer:{option}",
            )
        ]
        for option in options
    ]

    hint_buttons = []

    if show_hint:
        hint_buttons.append(
            InlineKeyboardButton(
                text="💡 Первая буква",
                callback_data="hint:first_letter",
            )
        )

    if show_map_hint:
        hint_buttons.append(
            InlineKeyboardButton(
                text="🗺️ Показать карту",
                callback_data="hint:map",
            )
        )

    if hint_buttons:
        keyboard.append(hint_buttons)

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


def next_question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Следующий вопрос",
                    callback_data="next_question",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="main_menu",
                )
            ],
        ]
    )