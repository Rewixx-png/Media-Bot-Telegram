# main.py

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from config import BOT_TOKEN, ADMIN_ID
from app.handlers import common, video_conv, audio_conv, video_to_audio

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    if not BOT_TOKEN:
        raise ValueError("Токен не найден! Проверьте .env файл.")

    # Локальный API
    custom_server = TelegramAPIServer.from_base('http://127.0.0.1:8081')
    session = AiohttpSession(api=custom_server)
    bot = Bot(token=BOT_TOKEN, session=session)

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    logging.info("Подключение роутеров...")
    
    # ВАЖНО: Сначала подключаем конкретные функции, чтобы они имели приоритет
    dp.include_router(video_conv.router)
    dp.include_router(audio_conv.router)
    dp.include_router(video_to_audio.router)
    
    # ВАЖНО: common подключаем ПОСЛЕДНИМ, т.к. там будет "ловушка" для всего остального
    dp.include_router(common.router)

    logging.info("Сброс вебхука...")
    await bot.delete_webhook(drop_pending_updates=True)

    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, "🟢 <b>Бот успешно перезапущен и готов к работе!</b>", parse_mode="HTML")
        except:
            logging.error("Не удалось отправить сообщение о запуске админу.")

    logging.info("Бот запущен нативно!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")