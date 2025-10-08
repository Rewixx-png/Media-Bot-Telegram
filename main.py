# Media_Bot/main.py

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from config import BOT_TOKEN
from app.handlers import common, video_conv, audio_conv, video_to_audio

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    if not BOT_TOKEN or BOT_TOKEN == "ВАШ_API_ТОКЕН_ЗДЕСЬ":
        logging.critical("Токен не найден или не изменен в файле config.py!")
        raise ValueError("Токен не найден или не изменен в файле config.py. Укажите его.")

    # --- ИЗМЕНЕНИЕ: Подключаемся к вашему удаленному API-серверу ---
    # Указываем протокол https:// для безопасности
    custom_server = TelegramAPIServer.from_base('https://api.rewixx.ru')
    session = AiohttpSession(api=custom_server)
    bot = Bot(token=BOT_TOKEN, session=session)
    # ----------------------------------------------------------------

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    logging.info("Подключение роутеров...")
    dp.include_router(common.router)
    dp.include_router(video_conv.router)
    dp.include_router(audio_conv.router)
    dp.include_router(video_to_audio.router)
    logging.info("Все роутеры успешно подключены.")

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
    except ValueError as e:
        print(e)