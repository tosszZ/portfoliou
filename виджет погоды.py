import tkinter as tk
from tkinter import ttk, messagebox
import requests

class WeatherAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Виджет погоды")
        self.root.geometry("400x300")
        
        self.api_key = "76ca06794ff81d9774a04ad2ad5d34d9"  # Замените на свой
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        
        self.create_widgets()
    
    def create_widgets(self):
        # Фрейм для ввода города
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="Город:").pack(side=tk.LEFT)
        self.city_entry = ttk.Entry(input_frame, width=20)
        self.city_entry.pack(side=tk.LEFT, padx=5)
        
        search_btn = ttk.Button(
            input_frame, 
            text="Узнать погоду", 
            command=self.fetch_weather
        )
        search_btn.pack(side=tk.LEFT)
        
        # Фрейм для отображения результатов
        self.result_frame = ttk.LabelFrame(
            self.root, 
            text="Результаты", 
            padding="10"
        )
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.weather_label = ttk.Label(
            self.result_frame, 
            text="Введите город и нажмите кнопку", 
            wraplength=350
        )
        self.weather_label.pack(fill=tk.BOTH, expand=True)
    
    def fetch_weather(self):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Ошибка!", "\nПожалуйста, введите город!")
            return
        
        try:
            params = {
                'q': city,# город 
                'appid': self.api_key,# API-ключ 
                'units': 'metric',# цельсия 
                'lang': 'ru',# язык 
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Извлекаем данные
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            pressure = data['main']['pressure']
            wind_speed = data['wind']['speed']
            description = data['weather'][0]['description'].capitalize()

            # Форматируем результат
            result = (f"Погода:\n"
                     f"Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                     f"Влажность: {humidity}%\n"
                     f"Давление: {pressure} гПа\n"
                     f"Ветер: {wind_speed} м/с\n"
                     f"Описание: {description}")
            
            self.weather_label.config(text=result)
            
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка", f"Не удалось получить данные: {e}")
        except KeyError:
            messagebox.showerror("Ошибка", "Неверный формат полученных данных")

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherAppGUI(root)
    root.mainloop()