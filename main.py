import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
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


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я погодный бот. Введите название города, чтобы узнать текущую погоду.")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def get_weather_by_city(message: types.Message):
    city = message.text.strip()

    weather_data = await get_weather(city)
    if weather_data is None:
        await message.reply("Не удалось найти информацию о погоде для данного города. Пожалуйста, проверьте правильность написания названия города.")
    else:
        weather_str = format_weather(weather_data)
        await message.reply(weather_str, parse_mode=ParseMode.HTML)


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
