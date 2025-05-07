import requests

def get_weather(city, api_key):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return f"Погода в {city}: {data['main']['temp']}°C"
        elif response.status_code == 401:
            return "Ошибка: неверный API-ключ"
        elif response.status_code == 404:
            return "Ошибка: город не найден"
        else:
            return f"Ошибка сервера: {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return f"Ошибка соединения: {e}"

# Пример использования
api_key = "76ca06794ff81d9774a04ad2ad5d34d9"  # 
city = "Анапа"  # Используйте английское название

result = get_weather(city, api_key)
print(result)