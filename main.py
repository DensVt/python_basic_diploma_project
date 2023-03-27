import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import ClientSession
import asyncio
import os
from datetime import datetime
from config import API_TOKEN, OPENWEATHERMAP_API_KEY


async def get_weather(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang=ru"

    async with ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data.get('cod') != 200:
                return None
            return data


async def get_forecast(city: str, days: int = 1):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang=ru"

    async with ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data.get('cod') != "200":
                return None
            return data


def format_weather(data):
    city = data['name']
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    description = data['weather'][0]['description']
    weather_id = data['weather'][0]['id']

    if 200 <= weather_id <= 232:
        weather_icon = "⛈️"  # Гроза
    elif 300 <= weather_id <= 531:
        weather_icon = "🌧️"  # Дождь
    elif 600 <= weather_id <= 622:
        weather_icon = "❄️"  # Снег
    elif 800 == weather_id:
        weather_icon = "☀️"  # Ясно
    else:
        weather_icon = "☁️"  # Облачно

    weather_str = f"{city}:\n{weather_icon} Температура: {temp}°C\nОщущается как: {feels_like}°C\n{description.capitalize()}"

    return weather_str


def format_forecast(data, days=1):
    city = data['city']['name']
    weather_list = data['list']

    if days == 1:
        period = "сегодня"
    elif days == 2:
        period = "завтра"
    else:
        period = f"следующие {days} дней"

    forecast_str = f"Прогноз погоды в {city} на {period}:\n"

    for i, weather_data in enumerate(weather_list[::8][:days]):
        date = weather_data['dt_txt'][:10]
        temp = weather_data['main']['temp']
        description = weather_data['weather'][0]['description']
        weather_id = weather_data['weather'][0]['id']

        if 200 <= weather_id <= 232:
            weather_icon = "⛈️"  # Гроза
        elif 300 <= weather_id <= 531:
            weather_icon = "🌧️"  # Дождь
        elif 600 <= weather_id <= 622:
            weather_icon = "❄️"  # Снег
        elif 800 == weather_id:
            weather_icon = "☀️"  # Ясно
        else:
            weather_icon = "☁️"  # Облачно

        forecast_str += f"{date}: {weather_icon} Температура: {temp}°C, {description.capitalize()}\n"

    return forecast_str

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


async def send_forecast_buttons(chat_id, city):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Сегодня", callback_data=f"today:{city}"),
        InlineKeyboardButton("Завтра", callback_data=f"tomorrow:{city}"),
    )
    keyboard.add(
        InlineKeyboardButton("Неделя", callback_data=f"week:{city}"),
        InlineKeyboardButton("История", callback_data="history"),
    )

    await bot.send_message(chat_id, "Выберите период прогноза:", reply_markup=keyboard)


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
    await bot.send_message(callback_query.from_user.id, forecast_str)


async def send_help_message(chat_id):
    help_text = (
        "Для того, чтобы получить информацию о погоде, введите название города.\n"
        "Я предоставлю вам прогноз погоды на сегодня, завтра и неделю вперед.\n"
        "Вы также сможете увидеть историю своих запросов."
    )
    await bot.send_message(chat_id, help_text)


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    start_text = (
        "Привет! Я погодный бот. Я могу предоставить информацию о погоде "
        "в разных городах, а также показать историю ваших запросов.\n"
        "Если вам нужна помощь, нажмите на кнопку /help ниже."
    )
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("Помощь", callback_data="help"))
    await bot.send_message(message.chat.id, start_text, reply_markup=keyboard)


@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    await send_help_message(message.chat.id)

@dp.callback_query_handler(lambda c: c.data == "help")
async def process_help(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await send_help_message(callback_query.from_user.id)


@dp.message_handler()
async def process_city(message: types.Message):
    city = message.text
    weather_data = await get_weather(city)

    if not weather_data:
        await message.reply(f"🚫 {city} не найден. Пожалуйста, проверьте название города и попробуйте еще раз.")
        return

    add_to_history(message.from_user.id, city)
    await send_forecast_buttons(message.chat.id, city)


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
    await bot.send_message(user_id, history_text)


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
    await bot.send_message(callback_query.from_user.id, forecast_str)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)