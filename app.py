from flask import Flask, render_template, request
import requests
import re

app = Flask(__name__)

API_KEY = 'l6276KnRGD8F0XaBMeyRrVe76oZ6OXVi'
BASE_URL = 'http://dataservice.accuweather.com/locations/v1/cities/search'
FORECAST_URL = 'http://dataservice.accuweather.com/forecasts/v1/daily/5day/'
CURRENT_CONDITIONS_URL = 'http://dataservice.accuweather.com/currentconditions/v1/'

# Функция для проверки, что введённое название состоит только из русских букв
def is_russian_city_name(city_name):
    pattern = r"^[А-ЯЁа-яё\s-]+$"
    return bool(re.match(pattern, city_name.strip()))

# Функция для получения кода города по названию
def get_city_code(city_name):
    if not is_russian_city_name(city_name):
        return None

    params = {
        'apikey': API_KEY,
        'q': city_name.strip(),
        'language': 'ru'
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200 and response.json():
        return response.json()[0]['Key']

    return None

# Функция для получения прогноза погоды по коду города
def get_weather_forecast(city_code, days=1):
    url = f"{FORECAST_URL}{city_code}"
    params = {
        'apikey': API_KEY,
        'metric': True
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# Функция для получения текущих погодных условий
def get_current_conditions(city_code):
    url = f"{CURRENT_CONDITIONS_URL}{city_code}"
    params = {
        'apikey': API_KEY,
        'language': 'ru',
        'details': 'true'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

# Логика определения неблагоприятных условий и возвращения детальной информации
def check_bad_weather(forecast, current_conditions):
    temp = forecast['DailyForecasts'][0]['Temperature']['Maximum']['Value']

    wind_speed = current_conditions[0].get('Wind', {}).get('Speed', {}).get('Metric', {}).get('Value', 0)
    precipitation = current_conditions[0].get('HasPrecipitation', False)

    weather_status = "Благоприятная погода на маршруте"
    if temp < 5 or temp > 30 or wind_speed > 40 or precipitation:
        weather_status = "Неблагоприятная погода на маршруте"

    return {
        'status': weather_status,
        'temp': temp,
        'wind_speed': wind_speed,
        'precipitation': 100 if precipitation else 0
    }

# Главная страница
@app.route('/', methods=['GET', 'POST'])
def index():
    start_weather, end_weather, error = None, None, None
    if request.method == 'POST':
        start_city = request.form['start_city']
        end_city = request.form['end_city']

        # Проверяем, являются ли названия городов русскими
        if not is_russian_city_name(start_city) or not is_russian_city_name(end_city):
            error = "Ошибка: название города должно быть на русском языке."
        else:
            start_city_code = get_city_code(start_city)
            end_city_code = get_city_code(end_city)

            if not start_city_code or not end_city_code:
                error = "Ошибка: неверно введён город или сервис временно не доступен"
            else:
                start_forecast = get_weather_forecast(start_city_code)
                end_forecast = get_weather_forecast(end_city_code)

                start_current = get_current_conditions(start_city_code)
                end_current = get_current_conditions(end_city_code)

                if not start_forecast or not end_forecast or not start_current or not end_current:
                    error = "Ошибка получения данных погоды или сервис временно не доступен"
                else:
                    start_weather = check_bad_weather(start_forecast, start_current)
                    end_weather = check_bad_weather(end_forecast, end_current)

    return render_template('index.html',
                           start_weather=start_weather,
                           end_weather=end_weather,
                           error=error)

# Обработка запроса для 5-дневного прогноза
@app.route('/forecast', methods=['POST'])
def forecast():
    start_city = request.form['start_city']
    end_city = request.form['end_city']
    start_forecast, end_forecast, error = None, None, None
    if not is_russian_city_name(start_city) or not is_russian_city_name(end_city):
        error = "Ошибка: название города должно быть на русском языке."
    else:
        start_city_code = get_city_code(start_city)
        end_city_code = get_city_code(end_city)

        if not start_city_code or not end_city_code:
            error = "Ошибка: неверно введён город или сервис временно не доступен"
        else:
            start_forecast = get_weather_forecast(start_city_code, days=5)
            end_forecast = get_weather_forecast(end_city_code, days=5)

            if not start_forecast or not end_forecast:
                error = "Ошибка получения данных погоды или сервис временно не доступен"

    return render_template('forecast.html',
                           start_forecast=start_forecast,
                           end_forecast=end_forecast,
                           error=error)

if __name__ == '__main__':
    app.run(debug=True)
