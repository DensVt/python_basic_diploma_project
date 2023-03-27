import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from datetime import datetime
from keyboards import forecast_buttons, help_button
from API import get_weather, get_forecast, format_weather, format_forecast
from config import API_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

user_history = {}

def add_to_history(user_id, city):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append((city, timestamp))

async def send_help_message(chat_id):
    help_text = (
        "Для того, чтобы получить информацию о погоде, введите название города.\n"
        "Я предоставлю вам прогноз погоды на сегодня, завтра и неделю вперед.\n"
        "Вы также сможете увидеть историю своих запросов."
    )
    await bot.send_message(chat_id, help_text, reply_markup=help_button())


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_name = message.from_user.username or message.from_user.first_name
    welcome_text = f"Привет, {user_name}! Я погодный бот. Я могу предоставить информацию о погоде в разных городах, а также показать историю ваших запросов. Если вам нужна помощь, нажмите на кнопку ниже.\n"
    
    help_button = types.InlineKeyboardButton("Помощь", callback_data="help")
    help_markup = types.InlineKeyboardMarkup().add(help_button)

    await message.reply(welcome_text, reply_markup=help_markup)


@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await send_help_message(message.chat.id)


@dp.callback_query_handler(lambda c: c.data == "help")
async def process_help(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await send_help_message(callback_query.message.chat.id)


@dp.message_handler()
async def process_city(message: types.Message):
    city = message.text
    weather_data = await get_weather(city)

    if not weather_data:
        await message.reply(f"🚫 {city} не найден. Пожалуйста, проверьте название города и попробуйте еще раз.")
        return

    add_to_history(message.from_user.id, city)
    keyboard = forecast_buttons(city)
    await bot.send_message(message.chat.id, "Выберите период прогноза:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == "history")
async def process_history(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_history or not user_history[user_id]:
        history_text = "История пуста."
    else:
        history_text = "История запросов:\n"
        for city, timestamp in user_history[user_id]:
            history_text += f"{timestamp}: {city}\n"

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.message.chat.id, history_text)


@dp.callback_query_handler(lambda c: c.data.startswith(('today:', 'tomorrow:', 'week:')))
async def process_callback(callback_query: types.CallbackQuery):
    command, city = callback_query.data.split(':', 1)

    if command == 'today':
        days = 1
    elif command == 'tomorrow':
        days = 2
    else:
        days = 7

    forecast_data = await get_forecast(city, days)
    if not forecast_data:
        await bot.answer_callback_query(callback_query.id, "Не удалось получить информацию о погоде. Проверьте название города и попробуйте еще раз.")
        return

    forecast_str = format_forecast(forecast_data, days)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.message.chat.id, forecast_str)