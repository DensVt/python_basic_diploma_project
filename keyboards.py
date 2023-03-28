from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def forecast_buttons(city):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Сегодня", callback_data=f"today:{city}"),
        InlineKeyboardButton("Завтра", callback_data=f"tomorrow:{city}"),
    )
    keyboard.add(
        InlineKeyboardButton("Неделя", callback_data=f"week:{city}"),
        InlineKeyboardButton("История", callback_data="history"),
    )

    return keyboard


def help_button():
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("Помощь", callback_data="help"))
