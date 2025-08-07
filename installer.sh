#!/bin/bash

# Выходим из скрипта, если любая команда завершится с ошибкой
set -e

echo "🚀 Начинаем установку Media Bot и локального Telegram API сервера..."

# --- 1. Сбор информации от пользователя ---
echo "⚙️ Пожалуйста, введите ваши данные от Telegram."
read -p "Введите ваш API ID: " API_ID
read -p "Введите ваш API HASH: " API_HASH
read -p "Введите ваш BOT TOKEN: " BOT_TOKEN

API_PORT=8088
PROJECT_PATH=$(pwd)

# --- 2. Установка системных зависимостей ---
echo "📦 Обновляем пакеты и устанавливаем зависимости..."
sudo apt-get update
sudo apt-get install -y g++ cmake make zlib1g-dev libssl-dev git python3-pip python3-venv ffmpeg

# --- 3. Сборка Telegram API Server ---
echo "🏗️ Скачиваем и собираем Telegram API сервер из исходников..."
if [ -d "telegram-bot-api" ]; then
    echo "Директория telegram-bot-api уже существует, пропускаем скачивание."
else
    git clone https://github.com/tdlib/telegram-bot-api.git
fi
cd telegram-bot-api
git submodule update --init --recursive
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --target install
cd $PROJECT_PATH # Возвращаемся в корневую папку проекта

echo "✅ Telegram API сервер успешно собран."

# --- 4. Создание systemd сервиса для API сервера ---
echo "🔧 Создаем systemd сервис для API сервера (telegram-api.service)..."

cat << EOF > /etc/systemd/system/telegram-api.service
[Unit]
Description=Telegram Bot API Server
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/telegram-bot-api --api-id=${API_ID} --api-hash=${API_HASH} --local --http-port=${API_PORT}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Перезагружаем демоны systemd и запускаем сервис API..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-api.service
sudo systemctl start telegram-api.service

echo "✅ Сервис API запущен и добавлен в автозагрузку."

# --- 5. Настройка окружения для бота ---
echo "🐍 Настраиваем Python окружение для бота..."
if [ -d "venv" ]; then
    echo "Виртуальное окружение venv уже существует."
else
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

# Записываем токен в config.py
echo "BOT_TOKEN = \"${BOT_TOKEN}\"" > config.py

echo "✅ Окружение бота настроено."

# --- 6. Создание systemd сервиса для бота ---
echo "🔧 Создаем systemd сервис для бота (media-bot.service)..."

cat << EOF > /etc/systemd/system/media-bot.service
[Unit]
Description=Media Bot for Telegram
After=telegram-api.service

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_PATH}
ExecStart=${PROJECT_PATH}/venv/bin/python3 ${PROJECT_PATH}/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Перезагружаем демоны systemd и запускаем сервис бота..."
sudo systemctl daemon-reload
sudo systemctl enable media-bot.service
sudo systemctl start media-bot.service

# --- Завершение ---
echo "🎉 УСТАНОВКА ЗАВЕРШЕНА! 🎉"
echo "Бот и API сервер запущены как сервисы."
echo "Проверить статус API: sudo systemctl status telegram-api"
echo "Проверить статус бота: sudo systemctl status media-bot"