from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def order_panel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Сделать новый заказ")],
            [KeyboardButton(text="Посмотреть свои заказы")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def products_keyboard(products: list, selected: dict = None) -> ReplyKeyboardMarkup:
    buttons = []
    selected = selected or {}
    for product in products:
        name = product.get("name", "") if isinstance(product, dict) else str(product)
        label = f"{name} ({selected[name]} шт.)" if name in selected else name
        buttons.append([KeyboardButton(text=label)])
    buttons.append([KeyboardButton(text="✅ Закончить выбор")])
    buttons.append([KeyboardButton(text="Отменить")])
    return ReplyKeyboardMarkup(
        keyboard=buttons, resize_keyboard=True, one_time_keyboard=False
    )


def order_confirmation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить заказ"), KeyboardButton(text="Отменить")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
