#!/bin/bash

# --- Цвета для вывода ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- Автоматический установщик Media Bot ---${NC}"

# --- Шаг 1: Обновление и установка необходимых пакетов ---
echo -e "\n${YELLOW}>>> Шаг 1: Установка зависимостей...${NC}"
sudo apt-get update
# Список зависимостей сокращен, так как компиляция больше не нужна
sudo apt-get install -y python3-pip python3-venv ffmpeg nodejs

# --- Шаг 2: Запрос данных у пользователя ---
echo -e "\n${YELLOW}>>> Шаг 2: Введите ваш токен бота...${NC}"
# API_ID и API_HASH больше не нужны
read -p "Введите ваш BOT_TOKEN: " BOT_TOKEN

# --- Шаг 3: Настройка Python-окружения ---
echo -e "\n${YELLOW}>>> Шаг 3: Настройка Python-окружения...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
deactivate

# --- Замена токена в config.py ---
CONFIG_FILE="config.py"
echo "BOT_TOKEN = \"$BOT_TOKEN\"" > $CONFIG_FILE

# --- Шаг 4: Настройка и запуск бота через PM2 ---
echo -e "\n${YELLOW}>>> Шаг 4: Настройка и запуск бота через PM2...${NC}"

# Проверка и установка PM2, если он не установлен
if ! command -v pm2 &> /dev/null; then
    echo "PM2 не найден. Устанавливаем PM2 глобально..."
    sudo npm install pm2 -g
fi

# Запуск бота с помощью PM2
echo "Запускаем бота 'media-bot'..."
PYTHON_INTERPRETER="$(pwd)/venv/bin/python3"
pm2 delete media-bot &> /dev/null # Удаляем старый процесс для чистого старта
pm2 start main.py --name media-bot --interpreter $PYTHON_INTERPRETER

# Сохранение списка процессов и настройка автозапуска
pm2 save
env_path=$(which pm2)
sudo env PATH=$PATH:/usr/bin $env_path startup systemd -u $(whoami) --hp $(echo $HOME)

echo -e "\n${GREEN}--- УСТАНОВКА ЗАВЕРШЕНА! ---${NC}"
echo -e "✅ Бот настроен для работы с сервером ${YELLOW}api.rewixx.ru${NC}."
echo -e "✅ Процесс запущен через PM2 под именем ${YELLOW}media-bot${NC}."
echo -e "Используйте '${YELLOW}pm2 logs media-bot${NC}' для просмотра логов."