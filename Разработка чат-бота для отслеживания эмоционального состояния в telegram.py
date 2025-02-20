import telebot
import schedule
import time
import threading
import random
import sqlite3
import os
import sys

# подключение базы данных
conn = sqlite3.connect("mood.db", check_same_thread=False)
cursor = conn.cursor()

# создание таблицы, если она не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    good INTEGER DEFAULT 0,
    neutral_mood INTEGER DEFAULT 0,
    bad INTEGER DEFAULT 0,
    variable INTEGER DEFAULT 0
)   
''')
conn.commit()

api_token = '7832541367:AAH8ncvd3jFzPp3jrkGC9zS0dZa-aCK6wm0'  # бот
bot = telebot.TeleBot(api_token)

# случайные сообщения
random_sms = [
    "Каждый новый день — это новая возможность начать с чистого листа и сделать что-то удивительное.",
    "Ты — уникален, и в тебе есть силы, которые могут изменить мир вокруг!",
    "Помни, что даже самые маленькие шаги ведут к большим достижениям.",
    "Улыбка — это универсальный язык, который может сделать день лучше для тебя и окружающих.",
    "Не бойся мечтать! Твои мечты — это карта к твоему будущему.",
    "В каждом трудном моменте скрыт урок, который делает нас сильнее и мудрее.",
    "Окружай себя позитивными людьми, которые вдохновляют и поддерживают тебя.",
    "Позволь себе отдыхать и наслаждаться моментами счастья — они делают жизнь ярче!",
    "Каждый день находи время для того, что приносит тебе радость, будь то хобби или прогулка на свежем воздухе.",
    "Ты способен на большее, чем думаешь! Верь в себя и свои возможности.",
]

# добавление в базу юзеров
def add_user(user_id):
    """
    Добавляет пользователя в базу данных, если его там нет.

    Аргументы:
        user_id (str): Идентификатор пользователя в Telegram.
    
    Исключения:
        sqlite3.Error: Если произошла ошибка при взаимодействии с базой данных.
    """
    try:
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id) VALUES (?)
        ''', (user_id,))
        conn.commit()
        print(f"User {user_id} добавлен в базу данных.")
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении пользователя {user_id}: {e}")

# обновление настроения
def update_mood(user_id, mood):
    """
    Обновляет настроение пользователя в базе данных.

    Аргументы:
        user_id (str): Идентификатор пользователя в Telegram.
        mood (str): Тип настроения пользователя (Хорошее, Нейтральное, Плохое, Изменчивое).
    
    Исключения:
        sqlite3.Error: Если произошла ошибка при взаимодействии с базой данных.
    """
    mood_map = {
        'Хорошее': 'good',
        'Нейтральное': 'neutral_mood',
        'Плохое': 'bad',
        'Изменчивое': 'variable'
    }
    if mood in mood_map:
        try:
            query = f'''
            UPDATE users SET {mood_map[mood]} = {mood_map[mood]} + 1
            WHERE user_id = ?
            '''
            cursor.execute(query, (user_id,))
            conn.commit()
            print(f"Обновлено настроение пользователя {user_id}: {mood}")
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении настроения {mood} для пользователя {user_id}: {e}")

# получение данных пользователей
def get_data(user_id):
    """
    Получает данные о настроении пользователя из базы данных.

    Аргументы:
        user_id (str): Идентификатор пользователя в Telegram.

    Возвращает:
        tuple: Кортеж из значений настроений пользователя (good, neutral_mood, bad, variable).
    
    Исключения:
        sqlite3.Error: Если произошла ошибка при взаимодействии с базой данных.
    """
    try:
        cursor.execute('''
        SELECT good, neutral_mood, bad, variable FROM users WHERE user_id = ?
        ''', (user_id,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Ошибка при получении данных для пользователя {user_id}: {e}")
        return None

# кнопки и вопрос о настроении
def question(user_id):
    """
    Отправляет пользователю вопрос о настроении с кнопками для выбора.

    Аргументы:
        user_id (str): Идентификатор пользователя в Telegram.
    """
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ['Хорошее', 'Нейтральное', 'Плохое', 'Изменчивое']
    markup.add(*buttons)
    bot.send_message(user_id, "Какое у вас настроение сегодня?", reply_markup=markup)

# обновление счёта настроения
def collect_mood(message):
    """
    Обрабатывает ответ пользователя и обновляет его настроение в базе данных.

    Аргументы:
        message (telebot.types.Message): Сообщение от пользователя.
    """
    user_id = str(message.chat.id)
    mood = message.text
    add_user(user_id)  # добавление пользователя в базу данных
    if mood in ['Хорошее', 'Нейтральное', 'Плохое', 'Изменчивое']:
        update_mood(user_id, mood)
        markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(user_id, f"Ваше настроение '{mood}' добавлено. Спасибо!", reply_markup=markup)
    else:
        chosen_sms = random.choice(random_sms)
        bot.send_message(user_id, chosen_sms)

# отчёт за неделю
def week_report(user_id):
    """
    Отправляет пользователю отчёт о его настроении за неделю.

    Аргументы:
        user_id (str): Идентификатор пользователя в Telegram.
    """
    data = get_data(user_id)
    if data:
        good, neutral, bad, variable = data
        report = (f"Твои ответы за неделю:\n"
                  f"Хорошее: {good}\n"
                  f"Нейтральное: {neutral}\n"
                  f"Плохое: {bad}\n"
                  f"Изменчивое: {variable}\n"
                  "Рекомендации:\n" + recom(good, bad, variable))
        bot.send_message(user_id, report)

# рекомендации по изменению настроения
def recom(good, bad, variable):
    """
    Предлагает рекомендации на основе данных о настроении пользователя.

    Аргументы:
        good (int): Количество "хороших" настроений.
        bad (int): Количество "плохих" настроений.
        variable (int): Количество "изменчивых" настроений.

    Возвращает:
        str: Рекомендации для пользователя.
    """
    if bad >= good and bad >= variable:
        return "Попробуйте заняться тем, что вам нравится, чтобы улучшить настроение."
    elif good >= bad and good >= variable:
        return "Продолжайте в том же духе! Вы на верном пути."
    elif variable > good and variable > bad:
        return "Попробуйте найти способы стабилизировать своё настроение. Возможно, поможет распорядок дня."
    else:
        return "Найдите время для отдыха и занятий, которые приносят радость."

# обработка сообщения
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """
    Обрабатывает любое входящее сообщение от пользователя и запускает функцию для сбора настроения.

    Аргументы:
        message (telebot.types.Message): Сообщение от пользователя.
    """
    collect_mood(message)

# вывод содержимого бд в консоль
def print_database():
    """
    Выводит содержимое базы данных пользователей в консоль.
    
    Исключения:
        sqlite3.Error: Если произошла ошибка при взаимодействии с базой данных.
    """
    try:
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        print("Содержимое базы данных:")
        for row in rows:
            print(row)
    except sqlite3.Error as e:
        print(f"Ошибка при выводе содержимого базы данных: {e}")

# вызов функции для вывода бд
print_database()

# вопрос при запуске
def send_daily_question():
    """
    Отправляет вопрос о настроении всем пользователям в базе данных каждый день.
    """
    users = cursor.execute('SELECT user_id FROM users').fetchall()
    for user_id, in users:
        try:
            question(user_id)
            print(f"Сообщение успешно отправлено пользователю {user_id}")
            time.sleep(0.1)  # Пауза в 100 мс для соблюдения лимитов
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

def send_weekly_report():
    """
    Отправляет еженедельный отчёт о настроении всем пользователям в базе данных.
    """
    users = cursor.execute('SELECT user_id FROM users').fetchall()
    for user_id, in users:
        try:
            week_report(user_id)
            print(f"Еженедельный отчёт отправлен пользователю {user_id}")
            time.sleep(0.1)  # Пауза в 100 мс для соблюдения лимитов
        except Exception as e:
            print(f"Не удалось отправить еженедельный отчёт пользователю {user_id}: {e}")

schedule.every().day.at("10:30").do(send_daily_question)
schedule.every().day.at("17:30").do(send_daily_question)
schedule.every().sunday.at("18:00").do(send_weekly_report)

# проверка на задачи
def run_schedule():                          
    """
    Запускает выполнение задач по расписанию.

    Этот метод должен работать в отдельном потоке.
    """
    while True:
        schedule.run_pending()
        time.sleep(1)

# запуск планировщика в отдельном потоке
threading.Thread(target=run_schedule, daemon=True).start()

# функция для перезапуска бота
def restart_bot():
    """
    Перезапускает бота, если возникла ошибка.

    Этот метод перезапустит скрипт с помощью sys.execv.
    """
    print("Перезапуск бота...")
    os.execv(sys.executable, ['python'] + sys.argv)

# запуск бота с тайм-аутом
try:
    bot.polling(none_stop=True, timeout=10)
except Exception as e:
    print(f"Ошибка при работе с ботом: {e}")
    restart_bot()

# закрытие соединения с бд
conn.close()
