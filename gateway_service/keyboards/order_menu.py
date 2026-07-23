from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def order_confirmation_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения заказа (пользовательская)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить заказ"), KeyboardButton(text="Отменить")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )