from aiohttp import ClientSession
from config import OPENWEATHERMAP_API_KEY
from datetime import datetime, timedelta

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
    temp = round(data['main']['temp'])  # Округление температуры до целых
    feels_like = round(data['main']['feels_like'])  # Округление ощущаемой температуры до целых
    description = data['weather'][0]['description']
    weather_id = data['weather'][0]['id']

    sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
    sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')
    day_duration = timedelta(seconds=data['sys']['sunset'] - data['sys']['sunrise'])
    day_duration_str = f"{day_duration.seconds // 3600} ч {day_duration.seconds % 3600 // 60} мин"

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

    weather_str = f"{city}:\n{weather_icon} Температура: {temp}°C\nОщущается как: {feels_like}°C\n{description.capitalize()}\nВосход солнца: {sunrise}\nЗакат солнца: {sunset}\nПродолжительность дня: {day_duration_str}\nХорошего дня, сэр! 🙂"

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

    city_sunrise = datetime.fromtimestamp(data['city']['sunrise']).strftime('%H:%M')
    city_sunset = datetime.fromtimestamp(data['city']['sunset']).strftime('%H:%M')
    city_day_duration = timedelta(seconds=data['city']['sunset'] - data['city']['sunrise'])
    city_day_duration_str = f"{city_day_duration.seconds // 3600} ч {city_day_duration.seconds % 3600 // 60} мин"

    for i, weather_data in enumerate(weather_list[::8][:days]):
        date = weather_data['dt_txt'][:10]
        temp = round(weather_data['main']['temp'])
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

        forecast_str += f"{date}: {weather_icon} Температура: {temp}°C, {description.capitalize()}\nВосход солнца: {city_sunrise}\nЗакат солнца: {city_sunset}\nПродолжительность дня: {city_day_duration_str}\nХорошего дня, сэр! 🙂\n"

    return forecast_str
