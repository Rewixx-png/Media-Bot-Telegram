# app/handlers/common.py

import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_ID
from app.keyboards.inline import get_main_menu
from app.states.conversion import ConversionStates

router = Router()
BANNER_PATH = "assets/banner.png"

@router.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    logging.info(f"--- START от {message.from_user.id} ---")
    await state.clear()

    caption_text = (
        "Добро пожаловать в Медиа-Мастерскую! ✨\n\n"
        "Я умею превращать видео и гифки в кружки, а также конвертировать аудио.\n"
        "Работаю через локальный сервер, лимитов нет! 🚀\n\n"
        "Выберите действие:"
    )

    try:
        if hasattr(FSInputFile(BANNER_PATH), 'path'): # Проверка пути
            await message.answer_photo(
                photo=FSInputFile(BANNER_PATH),
                caption=caption_text,
                reply_markup=get_main_menu()
            )
        else:
             await message.answer(caption_text, reply_markup=get_main_menu())
    except Exception as e:
        logging.error(f"Ошибка баннера: {e}")
        await message.answer(caption_text, reply_markup=get_main_menu())


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    caption_text = "Выберите действие:"
    
    try:
        await callback.message.edit_media(
            media=types.InputMediaPhoto(media=FSInputFile(BANNER_PATH), caption=caption_text),
            reply_markup=get_main_menu()
        )
    except Exception:
        # Если не вышло отредактировать (например, сообщение старое), шлем новое
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=FSInputFile(BANNER_PATH),
            caption=caption_text,
            reply_markup=get_main_menu()
        )
    await callback.answer()


# --- FALLBACK HANDLERS (ЛОВУШКИ ДЛЯ ОШИБОК) ---
# Если ни один роутер выше не поймал апдейт, он упадет сюда.

@router.callback_query()
async def unhandled_callbacks(callback: types.CallbackQuery, bot: Bot):
    """Ловит нажатия кнопок, которые не обработаны."""
    err_msg = f"⚠️ <b>UNHANDLED CALLBACK</b>\nUser: {callback.from_user.id}\nData: <code>{callback.data}</code>"
    logging.warning(err_msg)
    
    await callback.answer("Ошибка: Кнопка не обработана. Админ уведомлен.", show_alert=True)
    
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, err_msg, parse_mode="HTML")
        except:
            pass

@router.message()
async def unhandled_messages(message: types.Message, bot: Bot):
    """Ловит сообщения, которые не попали ни в один фильтр."""
    # Игнорируем команды (они могли быть обработаны, но фильтр passed)
    if message.text and message.text.startswith("/"):
        return

    err_msg = f"⚠️ <b>UNHANDLED MESSAGE</b>\nUser: {message.from_user.id}\nContent: {message.content_type}"
    logging.warning(err_msg)
    
    if ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID, err_msg, parse_mode="HTML")
        except:
            pass