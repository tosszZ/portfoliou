import telebot
from telebot import types
import json
import os
import re
from datetime import datetime
import requests
import time

# Конфигурация
BOT_TOKEN = '8531052521:AAEJhknJO78KGtyL-gYbflSmv4aBg3f83AM'  # Замените на ваш токен
DATA_FILE = 'tiktok_data.json'

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Структура для хранения данных
user_data = {}


def load_data():
    """Загрузка данных из файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}


def save_data():
    """Сохранение данных в файл"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)


# Загружаем данные при старте
user_data = load_data()


def get_user_data(user_id):
    """Получение данных пользователя"""
    user_id_str = str(user_id)
    if user_id_str not in user_data:
        user_data[user_id_str] = {
            'accounts': [],
            'last_update': None
        }
    return user_data[user_id_str]


def get_tiktok_stats(username):
    """
    Оптимальный метод получения статистики TikTok
    Использует несколько подходов для надежности
    """
    print(f"\n🔍 Получение данных для @{username}")

    # Сначала пробуем метод с Selenium (самый надежный)
    data = get_tiktok_selenium_simple(username)
    if data and data.get('followers', 0) > 0:
        print(f"✅ Данные получены через Selenium: {data}")
        return data

    # Если Selenium не сработал, пробуем API методы
    data = get_tiktok_api_method(username)
    if data and data.get('followers', 0) > 0:
        print(f"✅ Данные получены через API: {data}")
        return data

    # Последний вариант - парсинг страницы
    data = get_tiktok_direct_parse(username)
    if data and data.get('followers', 0) > 0:
        print(f"✅ Данные получены через парсинг: {data}")
        return data

    print(f"❌ Не удалось получить данные для @{username}")
    return {
        'followers': 0,
        'following': 0,
        'likes': 0,
        'videos': 0,
        'nickname': username
    }


def get_tiktok_selenium_simple(username):
    """
    Упрощенный метод через Selenium (самый надежный)
    Требует установки: pip install selenium webdriver-manager
    """
    try:
        # Пробуем импортировать Selenium
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options

        print("🔄 Использую Selenium...")

        # Настройка Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Фоновый режим
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Отключаем logging
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # Автоматическая установка драйвера
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            url = f'https://www.tiktok.com/@{username}'
            driver.get(url)

            # Ждем загрузки
            time.sleep(3)

            # Получаем исходный код
            html = driver.page_source

            # Ищем данные в разных форматах
            data = {}

            # Паттерн 1: Основные данные в JSON
            patterns = [
                (r'"followerCount":(\d+)', 'followers'),
                (r'"followingCount":(\d+)', 'following'),
                (r'"heartCount":(\d+)', 'likes'),
                (r'"videoCount":(\d+)', 'videos'),
                (r'"nickname":"([^"]+)"', 'nickname'),
                (r'"uniqueId":"([^"]+)"', 'username_check'),
            ]

            for pattern, key in patterns:
                matches = re.findall(pattern, html)
                if matches:
                    if key in ['nickname', 'username_check']:
                        data[key] = matches[0]
                    else:
                        data[key] = int(matches[0])

            # Если нашли данные
            if data:
                if 'nickname' not in data:
                    data['nickname'] = username

                # Заполняем пропущенные значения
                for key in ['followers', 'following', 'likes', 'videos']:
                    if key not in data:
                        data[key] = 0

                return data

        finally:
            driver.quit()

    except Exception as e:
        print(f"⚠️ Selenium не доступен: {e}")
        print("Установите: pip install selenium webdriver-manager")
        return None


def get_tiktok_api_method(username):
    """
    Метод через публичные API эндпоинты
    Не требует дополнительных библиотек
    """
    print("🔄 Использую API метод...")

    # Популярные API эндпоинты
    endpoints = [
        f'https://www.tiktok.com/node/share/user/@{username}',
        f'https://m.tiktok.com/api/user/detail/?uniqueId={username}',
        f'https://tiktok.com/node/share/user/@{username}',
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
        'Referer': 'https://www.tiktok.com/',
        'Origin': 'https://www.tiktok.com',
    }

    for endpoint in endpoints:
        try:
            print(f"  Пробуем: {endpoint}")
            response = requests.get(endpoint, headers=headers, timeout=10)

            if response.status_code == 200:
                json_data = response.json()

                # Разные форматы ответов
                data = extract_from_json(json_data, username)
                if data:
                    return data

        except Exception as e:
            print(f"  Ошибка: {e}")
            continue

    return None


def extract_from_json(json_data, username):
    """Извлечение данных из различных JSON структур"""
    data = {}

    # Формат 1: userInfo.stats
    if 'userInfo' in json_data:
        user_info = json_data['userInfo']
        stats = user_info.get('stats', {})

        data = {
            'followers': stats.get('followerCount', 0),
            'following': stats.get('followingCount', 0),
            'likes': stats.get('heartCount', 0),
            'videos': stats.get('videoCount', 0),
            'nickname': user_info.get('user', {}).get('nickname', username)
        }

    # Формат 2: body.userData
    elif 'body' in json_data and 'userData' in json_data['body']:
        user_data = json_data['body']['userData']
        stats = user_data.get('stats', {})

        data = {
            'followers': stats.get('followerCount', 0),
            'following': stats.get('followingCount', 0),
            'likes': stats.get('heartCount', 0),
            'videos': stats.get('videoCount', 0),
            'nickname': user_data.get('user', {}).get('nickname', username)
        }

    # Формат 3: Прямой user
    elif 'user' in json_data:
        user_data = json_data['user']
        stats = user_data.get('stats', {})

        data = {
            'followers': stats.get('followerCount', 0),
            'following': stats.get('followingCount', 0),
            'likes': stats.get('heartCount', 0),
            'videos': stats.get('videoCount', 0),
            'nickname': user_data.get('nickname', username)
        }

    # Проверяем что данные валидны
    if data and data.get('followers', 0) > 0:
        return data

    return None


def get_tiktok_direct_parse(username):
    """
    Прямой парсинг страницы через requests
    Резервный метод если API не работает
    """
    print("🔄 Использую прямой парсинг...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        url = f'https://www.tiktok.com/@{username}'
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None

        html = response.text

        # Ищем данные в тексте
        data = {}

        # Основные паттерны
        patterns = [
            (r'"followerCount":(\d+)', 'followers'),
            (r'"followingCount":(\d+)', 'following'),
            (r'"heartCount":(\d+)', 'likes'),
            (r'"videoCount":(\d+)', 'videos'),
            (r'"nickname":"([^"]+)"', 'nickname'),
        ]

        for pattern, key in patterns:
            matches = re.findall(pattern, html)
            if matches:
                if key == 'nickname':
                    data[key] = matches[0]
                else:
                    data[key] = int(matches[0])

        # Если нашли что-то
        if data:
            if 'nickname' not in data:
                data['nickname'] = username

            # Заполняем пропуски
            for key in ['followers', 'following', 'likes', 'videos']:
                if key not in data:
                    data[key] = 0

            return data

    except Exception as e:
        print(f"  Ошибка парсинга: {e}")

    return None


def format_number(num):
    """Форматирование чисел для отображения"""
    if not isinstance(num, (int, float)):
        try:
            num = int(num)
        except:
            return "0"

    if num >= 1000000000:
        return f"{num / 1000000000:.1f} млрд"
    elif num >= 1000000:
        return f"{num / 1000000:.1f} млн"
    elif num >= 1000:
        return f"{num / 1000:.1f} тыс"
    return str(num)


# Основные команды бота
@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработка команды /start"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('📝 Добавить аккаунт')
    btn2 = types.KeyboardButton('📊 Показать аккаунты')
    btn3 = types.KeyboardButton('🔄 Обновить данные')
    btn4 = types.KeyboardButton('🗑️ Очистить список')
    btn5 = types.KeyboardButton('ℹ️ Помощь')
    markup.add(btn1, btn2, btn3, btn4, btn5)

    bot.send_message(
        message.chat.id,
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для отслеживания TikTok аккаунтов.\n"
        "Я могу помочь вам:\n"
        "• 📝 Добавлять аккаунты\n"
        "• 📊 Смотреть статистику\n"
        "• 🔄 Обновлять данные\n"
        "• 📈 Сортировать по подписчикам\n\n"
        "Используйте кнопки ниже или команды:",
        reply_markup=markup
    )

    bot.send_message(
        message.chat.id,
        "📋 Команды:\n"
        "/add - Добавить аккаунт\n"
        "/list - Список аккаунтов\n"
        "/update - Обновить все данные\n"
        "/clear - Очистить список\n"
        "/help - Помощь"
    )


@bot.message_handler(commands=['help'])
def help_command(message):
    """Помощь по боту"""
    help_text = """
📖 **Помощь по боту:**

1. **📝 Добавление аккаунта:**
   • Используйте /add или кнопку
   • Введите username без @
   • Пример: `khaby.lame`

2. **📊 Просмотр аккаунтов:**
   • Аккаунты сортируются по количеству подписчиков
   • Показывает всю статистику

3. **🔄 Обновление данных:**
   • Получает актуальную статистику
   • Может занять 1-2 минуты
   • Использует несколько методов для надежности

4. **📈 Особенности:**
   • Для получения данных используется Selenium (самый надежный)
   • Если Selenium не установлен, используются API методы
   • Требуется интернет-соединение

5. **⚙️ Установка Selenium:**

    **Поддерживаемые аккаунты:**
    • Любые публичные аккаунты TikTok
    • Приватные аккаунты не поддерживаются
    """

    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')


@bot.message_handler(commands=['add'])
def add_account_command(message):
    """Добавление нового аккаунта"""
    msg = bot.send_message(
        message.chat.id,
        "📝 Введите username аккаунта TikTok:\n"
        "(только имя, без @ и https://)\n\n"
        "Пример: khaby.lame"
    )
    bot.register_next_step_handler(msg, process_add_account)


def process_add_account(message):
    """Обработка добавления аккаунта"""
    username = message.text.strip().lower()
    user_id = message.from_user.id

    # Проверка username
    if not username:
        bot.send_message(message.chat.id, "❌ Username не может быть пустым!")
        return

    if ' ' in username or '/' in username or '@' in username:
        bot.send_message(
            message.chat.id,
            "❌ Некорректный username!\n"
            "Используйте только буквы, цифры, точки и подчеркивания.\n"
            "Пример: khaby.lame"
        )
        return

    user_info = get_user_data(user_id)

    # Проверка на дубликат
    for account in user_info['accounts']:
        if account['username'] == username:
            bot.send_message(message.chat.id, f"❌ Аккаунт @{username} уже есть в списке!")
            return

    # Добавляем аккаунт
    user_info['accounts'].append({
        'username': username,
        'followers': 0,
        'following': 0,
        'likes': 0,
        'videos': 0,
        'nickname': username,
        'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'last_updated': None
    })
    save_data()

    markup = types.InlineKeyboardMarkup()
    btn_get_data = types.InlineKeyboardButton(
        '🔄 Получить данные сейчас',
        callback_data=f'getdata_{username}'
    )
    markup.add(btn_get_data)

    bot.send_message(
        message.chat.id,
        f"✅ Аккаунт @{username} добавлен!\n\n"
        "Вы можете получить данные сейчас или позже через 'Обновить данные'.",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('getdata_'))
def callback_get_data(call):
    """Получение данных для одного аккаунта"""
    username = call.data.replace('getdata_', '')
    user_id = call.from_user.id
    user_info = get_user_data(user_id)

    # Находим аккаунт
    account = None
    for acc in user_info['accounts']:
        if acc['username'] == username:
            account = acc
            break

    if not account:
        bot.answer_callback_query(call.id, "❌ Аккаунт не найден!")
        return

    bot.answer_callback_query(call.id, "🔄 Получаю данные...")

    # Получаем данные
    data = get_tiktok_stats(username)

    if data and data.get('followers', 0) > 0:
        account['followers'] = data.get('followers', 0)
        account['following'] = data.get('following', 0)
        account['likes'] = data.get('likes', 0)
        account['videos'] = data.get('videos', 0)
        account['nickname'] = data.get('nickname', username)
        account['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data()

        bot.send_message(
            call.message.chat.id,
            f"✅ Данные для @{username} обновлены!\n\n"
            f"📊 **Статистика:**\n"
            f"• 👤 Подписчиков: {format_number(account['followers'])}\n"
            f"• 📈 Подписок: {format_number(account['following'])}\n"
            f"• ❤️ Лайков: {format_number(account['likes'])}\n"
            f"• 📹 Видео: {format_number(account['videos'])}\n"
            f"• 📝 Имя: {account['nickname']}\n\n"
            f"📅 Обновлено: {account['last_updated'][:16]}",
            parse_mode='Markdown'
        )
    else:
        bot.send_message(
            call.message.chat.id,
            f"❌ Не удалось получить данные для @{username}\n\n"
            "**Возможные причины:**\n"
            "• Аккаунт не существует\n"
            "• Аккаунт приватный\n"
            "• Проблемы с доступом к TikTok\n"
            "• Ошибка сети\n\n"
            "**Рекомендации:**\n"
            "1. Проверьте правильность username\n"
            "2. Установите Selenium для более надежной работы:\n"
            "   `pip install selenium webdriver-manager`\n"
            "3. Попробуйте позже",
            parse_mode='Markdown'
        )


@bot.message_handler(commands=['list'])
def list_accounts_command(message):
    """Показать список аккаунтов"""
    user_id = message.from_user.id
    user_info = get_user_data(user_id)

    if not user_info['accounts']:
        bot.send_message(
            message.chat.id,
            "📭 У вас нет добавленных аккаунтов.\n"
            "Используйте /add чтобы добавить первый аккаунт."
        )
        return

    # Сортируем по подписчикам
    sorted_accounts = sorted(
        user_info['accounts'],
        key=lambda x: x['followers'],
        reverse=True
    )

    # Создаем сообщение
    response = "📊 **ВАШИ TIKTOK АККАУНТЫ**\n"
    response += f"Всего: {len(sorted_accounts)} аккаунтов\n"
    response += "=" * 40 + "\n\n"

    total_followers = 0
    total_likes = 0
    total_videos = 0

    for i, account in enumerate(sorted_accounts, 1):
        total_followers += account['followers']
        total_likes += account['likes']
        total_videos += account['videos']

        response += f"**{i}. @{account['username']}**\n"

        if account['nickname'] and account['nickname'] != account['username']:
            response += f"   📝 {account['nickname']}\n"

        response += f"   👤 {format_number(account['followers'])} подписчиков\n"

        if account['following'] > 0:
            response += f"   📈 {format_number(account['following'])} подписок\n"

        if account['likes'] > 0:
            response += f"   ❤️ {format_number(account['likes'])} лайков\n"

        if account['videos'] > 0:
            response += f"   📹 {format_number(account['videos'])} видео\n"

        if account.get('last_updated'):
            response += f"   🕐 {account['last_updated'][:10]}\n"

        response += "\n"

    # Статистика
    response += "=" * 40 + "\n"
    response += "📈 **ОБЩАЯ СТАТИСТИКА:**\n"
    response += f"• Всего подписчиков: {format_number(total_followers)}\n"
    response += f"• Всего лайков: {format_number(total_likes)}\n"
    response += f"• Всего видео: {format_number(total_videos)}\n"
    response += f"• Среднее на аккаунт: {format_number(total_followers // max(1, len(sorted_accounts)))}\n\n"

    if user_info.get('last_update'):
        response += f"🔄 Последнее обновление: {user_info['last_update'][:16]}"

    # Кнопки управления
    markup = types.InlineKeyboardMarkup()
    btn_update = types.InlineKeyboardButton('🔄 Обновить все', callback_data='update_all')
    btn_export = types.InlineKeyboardButton('📤 Экспорт', callback_data='export_data')
    markup.add(btn_update, btn_export)

    # Отправляем сообщение
    if len(response) > 4000:
        parts = [response[i:i + 4000] for i in range(0, len(response), 4000)]
        for part in parts[:-1]:
            bot.send_message(message.chat.id, part, parse_mode='Markdown')
        bot.send_message(message.chat.id, parts[-1], parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, response, parse_mode='Markdown', reply_markup=markup)


@bot.message_handler(commands=['update'])
def update_all_command(message):
    """Обновление всех аккаунтов"""
    user_id = message.from_user.id
    user_info = get_user_data(user_id)

    if not user_info['accounts']:
        bot.send_message(message.chat.id, "❌ Нет аккаунтов для обновления!")
        return

    bot.send_message(
        message.chat.id,
        f"🔄 Начинаю обновление {len(user_info['accounts'])} аккаунтов...\n"
        "Это может занять 1-2 минуты. Пожалуйста, подождите."
    )

    updated_count = 0
    total = len(user_info['accounts'])

    # Создаем прогресс-бар
    progress_msg = bot.send_message(
        message.chat.id,
        f"📊 Прогресс: 0/{total} (0%)"
    )

    for i, account in enumerate(user_info['accounts'], 1):
        try:
            # Обновляем прогресс каждые 2 аккаунта
            if i % 2 == 0 or i == total:
                percent = int((i / total) * 100)
                bot.edit_message_text(
                    f"📊 Прогресс: {i}/{total} ({percent}%)\n"
                    f"Сейчас: @{account['username']}",
                    message.chat.id,
                    progress_msg.message_id
                )

            # Получаем данные с задержкой
            data = get_tiktok_stats(account['username'])
            time.sleep(1)  # Задержка чтобы не заблокировали

            if data and data.get('followers', 0) > 0:
                account['followers'] = data.get('followers', account['followers'])
                account['following'] = data.get('following', account['following'])
                account['likes'] = data.get('likes', account['likes'])
                account['videos'] = data.get('videos', account['videos'])
                account['nickname'] = data.get('nickname', account['username'])
                account['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated_count += 1

        except Exception as e:
            print(f"Ошибка при обновлении {account['username']}: {e}")
            continue

    user_info['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data()

    bot.edit_message_text(
        f"✅ Обновление завершено!\n\n"
        f"📊 **Результаты:**\n"
        f"• Обновлено: {updated_count}/{total}\n"
        f"• Не обновлено: {total - updated_count}\n\n"
        f"Используйте /list для просмотра обновленных данных.",
        message.chat.id,
        progress_msg.message_id,
        parse_mode='Markdown'
    )


@bot.callback_query_handler(func=lambda call: call.data == 'update_all')
def callback_update_all(call):
    """Callback для обновления всех"""
    update_all_command(call.message)


@bot.callback_query_handler(func=lambda call: call.data == 'export_data')
def callback_export_data(call):
    """Экспорт данных"""
    user_id = call.from_user.id
    user_info = get_user_data(user_id)

    if not user_info['accounts']:
        bot.answer_callback_query(call.id, "❌ Нет данных для экспорта!")
        return

    bot.answer_callback_query(call.id, "📥 Подготавливаю экспорт...")

    # Сортируем данные
    sorted_accounts = sorted(
        user_info['accounts'],
        key=lambda x: x['followers'],
        reverse=True
    )

    # Создаем файл
    filename = f"tiktok_export_{user_id}_{int(time.time())}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("ЭКСПОРТ TIKTOK АККАУНТОВ\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Пользователь: ID {user_id}\n")
        f.write(f"Дата экспорта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Всего аккаунтов: {len(sorted_accounts)}\n")
        f.write("=" * 60 + "\n\n")

        for i, account in enumerate(sorted_accounts, 1):
            f.write(f"{i:3d}. @{account['username']}\n")
            f.write(f"     Подписчики: {account['followers']:>12} ({format_number(account['followers'])})\n")
            f.write(f"     Подписки:   {account['following']:>12} ({format_number(account['following'])})\n")
            f.write(f"     Лайки:      {account['likes']:>12} ({format_number(account['likes'])})\n")
            f.write(f"     Видео:      {account['videos']:>12} ({format_number(account['videos'])})\n")

            if account.get('nickname') and account['nickname'] != account['username']:
                f.write(f"     Имя:        {account['nickname']}\n")

            f.write(f"     Добавлен:   {account['added_date'][:10]}\n")

            if account.get('last_updated'):
                f.write(f"     Обновлено:  {account['last_updated'][:10]}\n")

            f.write("\n")

    # Отправляем файл
    with open(filename, 'rb') as file:
        bot.send_document(
            call.message.chat.id,
            file,
            caption=f"📁 Экспорт TikTok аккаунтов\n"
                    f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                    f"📊 {len(sorted_accounts)} аккаунтов"
        )

    # Удаляем временный файл
    os.remove(filename)


@bot.message_handler(commands=['clear'])
def clear_command(message):
    """Очистка списка"""
    user_id = message.from_user.id
    user_info = get_user_data(user_id)

    if not user_info['accounts']:
        bot.send_message(message.chat.id, "📭 Список уже пуст!")
        return

    count = len(user_info['accounts'])

    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton('✅ Да, очистить', callback_data='clear_confirm')
    btn_no = types.InlineKeyboardButton('❌ Нет, отмена', callback_data='clear_cancel')
    markup.add(btn_yes, btn_no)

    bot.send_message(
        message.chat.id,
        f"⚠️ **ВНИМАНИЕ!**\n\n"
        f"Вы собираетесь удалить **ВСЕ** ({count}) аккаунтов.\n"
        f"Это действие нельзя отменить!\n\n"
        f"Вы уверены?",
        parse_mode='Markdown',
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('clear_'))
def callback_clear(call):
    """Обработка очистки"""
    if call.data == 'clear_confirm':
        user_id = call.from_user.id
        user_info = get_user_data(user_id)
        count = len(user_info['accounts'])

        user_info['accounts'] = []
        save_data()

        bot.edit_message_text(
            f"✅ Список очищен!\n"
            f"Удалено {count} аккаунтов.",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        bot.edit_message_text(
            "❌ Очистка отменена.",
            call.message.chat.id,
            call.message.message_id
        )


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Обработка всех текстовых сообщений"""
    text = message.text

    if text == '📝 Добавить аккаунт':
        add_account_command(message)
    elif text == '📊 Показать аккаунты':
        list_accounts_command(message)
    elif text == '🔄 Обновить данные':
        update_all_command(message)
    elif text == '🗑️ Очистить список':
        clear_command(message)
    elif text == 'ℹ️ Помощь':
        help_command(message)
    else:
        bot.send_message(
            message.chat.id,
            "Я понимаю только команды и кнопки меню.\n"
            "Используйте /help для справки."
        )


# Запуск бота
if __name__ == '__main__':
    print("=" * 50)
    print("🤖 TikTok Account Tracker Bot")
    print("=" * 50)
    print("Бот запущен...")
    print("Для остановки нажмите Ctrl+C")
    print("\nВажные заметки:")
    print("1. Для лучшей работы установите Selenium:")
    print("   pip install selenium webdriver-manager")
    print("2. Если Selenium не установлен, будут использоваться API методы")
    print("=" * 50)

    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка: {e}")
        print("Бот остановлен.")