from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def order_panel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура раздела 'Заказать'."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Сделать новый заказ")],
            [KeyboardButton(text="Посмотреть свои заказы")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )