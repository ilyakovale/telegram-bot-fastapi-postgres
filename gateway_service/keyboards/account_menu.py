from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def account_panel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура раздела 'Аккаунт'."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Изменить данные аккаунта")],
            [KeyboardButton(text="ℹ️ Данные аккаунта"), KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def confirmation_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения (Да/Нет)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )