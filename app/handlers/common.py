# app/handlers/common.py

import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile  # <--- ДОБАВЛЯЕМ ЭТОТ ИМПОРТ

from app.keyboards.inline import get_main_menu
from app.states.conversion import ConversionStates

router = Router()

# Путь к нашему баннеру
BANNER_PATH = "assets/banner.png"

@router.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    logging.info("--- Сработал хэндлер send_welcome ---")
    await state.clear()

    # Создаем объект файла для отправки
    banner = FSInputFile(BANNER_PATH)

    # Формируем текст для подписи к фото
    caption_text = (
        "Добро пожаловать в Медиа-Мастерскую! ✨\n\n"
        "Я умею превращать видео и гифки в кружки, а также конвертировать аудио.\n\n"
        "Выберите действие:"
    )

    # --- ИЗМЕНЕНИЕ: Отправляем фото с подписью вместо простого сообщения ---
    await message.answer_photo(
        photo=banner,
        caption=caption_text,
        reply_markup=get_main_menu()
    )
    # ----------------------------------------------------------------------

    # Старое сообщение можно удалить, если оно не нужно
    try:
        await message.delete()
    except Exception:
        pass # Игнорируем ошибку, если бот не может удалить сообщение (например, нет прав)
    
    logging.info("--- Хэндлер send_welcome завершен ---")


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"--- Сработал хэндлер back_to_main_menu, callback.data: '{callback.data}' ---")
    await state.clear()
    
    # Создаем объект файла для отправки
    banner = FSInputFile(BANNER_PATH)

    # Формируем текст для подписи к фото
    caption_text = (
        "Выберите действие:"
    )

    # --- ИЗМЕНЕНИЕ: При возврате в меню тоже показываем баннер ---
    # Мы используем answer_photo, чтобы отправить новое сообщение с картинкой,
    # а старое сообщение с кнопками будет автоматически удалено после ответа на callback.
    # Чтобы было еще красивее, можно отредактировать медиа, но это сложнее.
    # Просто отправим новое сообщение, это надежно.
    await callback.message.answer_photo(
        photo=banner,
        caption=caption_text,
        reply_markup=get_main_menu()
    )
    # Удаляем старое сообщение, от которого пришел колбэк
    await callback.message.delete()
    await callback.answer() # Отвечаем на колбэк, чтобы убрать "часики"
    
    logging.info("--- Хэндлер back_to_main_menu завершен ---")


# Универсальный обработчик неверного ввода в любом состоянии
@router.message(
    ConversionStates.waiting_for_media_for_circle,
    ConversionStates.waiting_for_audio_for_conversion,
    ConversionStates.waiting_for_video_for_audio_extraction
)
async def handle_wrong_input_in_state(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.warning(f"--- Сработал УНИВЕРСАЛЬНЫЙ хэндлер неправильного ввода ---")
    logging.warning(f"Пользователь {message.from_user.id} прислал некорректный тип данных в состоянии {current_state}")
    
    await message.reply(
        "Я ожидаю файл определённого типа для выбранной операции.\n\n"
        "Пожалуйста, отправьте нужный файл или начните заново с команды /start."
    )
    logging.warning("--- Универсальный хэндлер завершен ---")