import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import ClientSession
import asyncio
import os
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

async def send_forecast_buttons(chat_id, city):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Сегодня", callback_data=f"today:{city}"),
        InlineKeyboardButton("Завтра", callback_data=f"tomorrow:{city}"),
    )
    keyboard.add(InlineKeyboardButton("Неделя", callback_data=f"week:{city}"))

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


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я погодный бот. Введите название города, чтобы узнать прогноз погоды.")

@dp.message_handler()
async def process_city(message: types.Message):
    city = message.text
    await send_forecast_buttons(message.chat.id, city)  # Выводим кнопки после ввода города

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
