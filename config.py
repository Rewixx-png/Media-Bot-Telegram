# config.py

import os
from dotenv import load_dotenv

# Принудительно загружаем переменные из .env файла в текущей папке
load_dotenv()

# Забираем токен
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
LOCAL_API_PATH = os.getenv("LOCAL_API_PATH")
