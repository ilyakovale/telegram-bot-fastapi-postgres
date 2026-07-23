from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная панель администратора."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="🔒 Управление пользователями")],
            [KeyboardButton(text="📦 Управление заказами")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def admin_account_keyboard() -> ReplyKeyboardMarkup:
    """Подменю управления пользователями."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Заблокировать"), KeyboardButton(text="Разблокировать")],
            [KeyboardButton(text="Просмотреть всех"), KeyboardButton(text="◀️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def admin_order_keyboard() -> ReplyKeyboardMarkup:
    """Подменю управления заказами."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать новый заказ"), KeyboardButton(text="Просмотреть заказы")],
            [KeyboardButton(text="Удалить заказ"), KeyboardButton(text="◀️ Назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )