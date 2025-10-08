#!/bin/bash

# --- Цвета для вывода ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- Автоматический установщик Media Bot ---${NC}"

# --- Обновление пакетов и установка базовых зависимостей ---
echo -e "\n${YELLOW}>>> Шаг 1: Обновление системы и установка зависимостей...${NC}"
sudo apt-get update
# ИСПРАВЛЕНО: Добавлен 'cmake' и убран 'npm', чтобы избежать конфликта пакетов.
# 'npm' будет установлен вместе с 'nodejs'.
sudo apt-get install -y git build-essential g++ cmake libssl-dev zlib1g-dev \
                        python3-pip python3-venv ffmpeg nodejs

# --- Сборка и установка локального API-сервера Telegram ---
echo -e "\n${YELLOW}>>> Шаг 2: Настройка локального API-сервера Telegram...${NC}"
if [ -d "td" ]; then
    echo "Директория 'td' уже существует. Пропускаем клонирование."
else
    git clone https://github.com/tdlib/td.git
fi
cd td
git checkout v1.8.0
rm -rf build
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --target telegram-bot-api -- -j $(nproc)
cd ../..

# --- Запрос данных у пользователя ---
echo -e "\n${YELLOW}>>> Шаг 3: Введите ваши данные от Telegram...${NC}"
read -p "Введите ваш API_ID: " API_ID
read -p "Введите ваш API_HASH: " API_HASH
read -p "Введите ваш BOT_TOKEN: " BOT_TOKEN

# --- Создание systemd-сервиса для API-сервера ---
echo -e "\n${YELLOW}>>> Шаг 4: Создание systemd-сервиса для API-сервера...${NC}"
SERVICE_FILE="/etc/systemd/system/telegram-api.service"
cat << EOF | sudo tee $SERVICE_FILE
[Unit]
Description=Telegram Bot API Server
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)/td/build
ExecStart=$(pwd)/td/build/telegram-bot-api --api-id=$API_ID --api-hash=$API_HASH --local --http-port=8088
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable telegram-api.service
sudo systemctl restart telegram-api.service
echo -e "${GREEN}Сервис 'telegram-api' создан и запущен.${NC}"

# --- Настройка Python-окружения ---
echo -e "\n${YELLOW}>>> Шаг 5: Настройка Python-окружения...${NC}"
# Создаем venv, если его нет
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
deactivate

# --- Замена токена в config.py ---
CONFIG_FILE="config.py"
echo "BOT_TOKEN = \"$BOT_TOKEN\"" > $CONFIG_FILE

# --- Настройка и запуск бота через PM2 ---
echo -e "\n${YELLOW}>>> Шаг 6: Настройка и запуск бота через PM2...${NC}"

# Проверка и установка PM2, если он не установлен
if ! command -v pm2 &> /dev/null; then
    echo "PM2 не найден. Устанавливаем PM2 глобально..."
    sudo npm install pm2 -g
fi

# Запуск бота с помощью PM2
echo "Запускаем бота 'media-bot'..."
# Используем полный путь к интерпретатору из venv
PYTHON_INTERPRETER="$(pwd)/venv/bin/python3"
# Удаляем старый процесс, если он существует, для чистого старта
pm2 delete media-bot &> /dev/null
pm2 start main.py --name media-bot --interpreter $PYTHON_INTERPRETER

# Сохранение списка процессов и настройка автозапуска
pm2 save
# Настройка автозапуска PM2 при перезагрузке системы
# Команда `pm2 startup` выводит команду, которую нужно выполнить с sudo.
# Мы автоматизируем этот процесс.
env_path=$(which pm2)
sudo env PATH=$PATH:/usr/bin $env_path startup systemd -u $(whoami) --hp $(echo $HOME)

echo -e "\n${GREEN}--- УСТАНОВКА ЗАВЕРШЕНА! ---${NC}"
echo -e "✅ Локальный API-сервер Telegram запущен как сервис ${YELLOW}telegram-api${NC}."
echo -e "✅ Бот запущен через PM2 под именем ${YELLOW}media-bot${NC}."
echo -e "Используйте '${YELLOW}pm2 logs media-bot${NC}' для просмотра логов бота."