from flask import Flask, render_template, request
import requests
import re
from datetime import datetime

app = Flask(__name__)

API_KEY = 'r1owHcT8FNCpEDDJuHRAE1QAGETEBdsh'
BASE_URL = 'http://dataservice.accuweather.com/locations/v1/cities/search'
FORECAST_URL = 'http://dataservice.accuweather.com/forecasts/v1/daily/5day/'
CURRENT_CONDITIONS_URL = 'http://dataservice.accuweather.com/currentconditions/v1/'

def is_russian_city_name(city_name):
    """Check if the city name is in Russian."""
    pattern = r"^[А-ЯЁа-яё\s-]+$"
    return bool(re.match(pattern, city_name.strip()))

def get_city_code(city_name):
    """Retrieve the city code for a given Russian city name."""
    if not is_russian_city_name(city_name):
        return None

    params = {'apikey': API_KEY, 'q': city_name.strip(), 'language': 'ru'}
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200 and response.json():
        return response.json()[0]['Key']
    return None

def get_weather_forecast(city_code, days=5):
    """Fetch the weather forecast for a specified city code."""
    url = f"{FORECAST_URL}{city_code}"
    params = {'apikey': API_KEY, 'metric': True}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None

def format_forecast_date(forecast_data):
    """Format the date in the forecast data."""
    for day in forecast_data['DailyForecasts']:
        date_obj = datetime.fromisoformat(day['Date'][:10])
        day['FormattedDate'] = date_obj.strftime("%d.%m.%Y")
    return forecast_data

@app.route('/', methods=['GET', 'POST'])
def index():
    """Render the main page and handle form submissions."""
    start_weather, end_weather, additional_weathers, error = None, None, [], None

    if request.method == 'POST':
        start_city = request.form['start_city']
        end_city = request.form['end_city']
        additional_cities = [v for k, v in request.form.items() if k.startswith('additional_city')]

        if not all(is_russian_city_name(city) for city in [start_city, end_city] + additional_cities):
            error = "Ошибка: название города должно быть на русском языке."
        else:
            start_city_code = get_city_code(start_city)
            end_city_code = get_city_code(end_city)
            additional_codes = [get_city_code(city) for city in additional_cities]

            if not start_city_code or not end_city_code:
                error = "Ошибка: неверно введён город или сервис временно не доступен"
            else:
                start_weather = get_weather_forecast(start_city_code)
                end_weather = get_weather_forecast(end_city_code)
                print(start_weather, end_weather)
                if any(code is None for code in additional_codes):
                    error = "Ошибка: неверно введён промежуточный город или сервис временно не доступен"
                else:
                    additional_weathers = [get_weather_forecast(code) for code in additional_codes]

    return render_template('index.html', start_weather=start_weather, end_weather=end_weather, additional_weathers=additional_weathers, error=error)

if __name__ == '__main__':
    app.run(debug=True)
