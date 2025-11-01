# config.py

import os

# Забираем токен из переменных окружения.
# Если переменная не найдена, вернется None.
BOT_TOKEN = os.getenv("BOT_TOKEN")
