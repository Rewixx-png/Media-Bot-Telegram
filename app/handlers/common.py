# app/handlers/common.py

import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest

from app.keyboards.inline import get_main_menu
from app.states.conversion import ConversionStates

router = Router()

# Указываем правильный путь к вашему баннеру
BANNER_PATH = "assets/banner.png"

@router.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    """
    Отправляет ОДНО сообщение: баннер с подписью и кнопками.
    """
    logging.info("--- Сработал хэндлер send_welcome ---")
    await state.clear()

    banner = FSInputFile(BANNER_PATH)

    caption_text = (
        "Добро пожаловать в Медиа-Мастерскую! ✨\n\n"
        "Я умею превращать видео и гифки в кружки, а также конвертировать аудио.\n\n"
        "Выберите действие:"
    )

    # Единственная команда на отправку сообщения
    await message.answer_photo(
        photo=banner,
        caption=caption_text,
        reply_markup=get_main_menu()
    )
    logging.info("--- Хэндлер send_welcome завершен ---")


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """
    Возвращает пользователя в главное меню, редактируя существующее сообщение.
    """
    logging.info(f"--- Сработал хэндлер back_to_main_menu ---")
    await state.clear()
    
    banner = FSInputFile(BANNER_PATH)
    caption_text = "Выберите действие:"

    try:
        # Пытаемся отредактировать медиа и подпись
        await callback.message.edit_media(
            media=types.InputMediaPhoto(media=banner, caption=caption_text),
            reply_markup=get_main_menu()
        )
    except TelegramBadRequest:
        # Если не получилось (например, сообщение слишком старое), удаляем старое и отправляем новое
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=banner,
            caption=caption_text,
            reply_markup=get_main_menu()
        )
    
    await callback.answer()
    logging.info("--- Хэндлер back_to_main_menu завершен ---")


# Универсальный обработчик неверного ввода в любом состоянии
@router.message(
    ConversionStates.waiting_for_media_for_circle,
    ConversionStates.waiting_for_audio_for_conversion,
    ConversionStates.waiting_for_video_for_audio_extraction
)
async def handle_wrong_input_in_state(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.warning(f"Пользователь {message.from_user.id} прислал некорректный тип данных в состоянии {current_state}")
    
    await message.reply(
        "Я ожидаю файл определённого типа для выбранной операции.\n\n"
        "Пожалуйста, отправьте нужный файл или начните заново с команды /start."
    )