# Dockerfile

# Используем легкий базовый образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости, в первую очередь FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем сначала только файл с зависимостями, чтобы кэшировать этот слой
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта в рабочую директорию
COPY . .

# Команда для запуска бота при старте контейнера
CMD ["python", "main.py"]