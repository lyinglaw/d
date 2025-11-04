# Файл keep_alive.py
from flask import Flask
from threading import Thread
import logging

# Отключим лишний вывод логов Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    return "Bot is running with aiogram Long Polling!"

def run():
  # Запускаем Flask в отдельном потоке
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
