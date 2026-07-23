from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Заказать")],
            [KeyboardButton(text="ℹ️ Аккаунт"), KeyboardButton(text="📞 Контакты")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def back_to_main_keyboard() -> ReplyKeyboardMarkup:
    """Кнопка 'Назад' в главное меню (используется в подменю)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )