import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.keyboards.inline import get_main_menu
from app.states.conversion import ConversionStates

router = Router()

@router.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    logging.info("--- Сработал хэндлер send_welcome ---")
    await state.clear()
    await message.answer(
        "Добро пожаловать в Медиа-Мастерскую! ✨\n\n"
        "Я умею превращать видео и гифки в кружки, а также конвертировать аудио.\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu()
    )
    try:
        await message.delete()
    except Exception:
        pass
    logging.info("--- Хэндлер send_welcome завершен ---")


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"--- Сработал хэндлер back_to_main_menu, callback.data: '{callback.data}' ---")
    await state.clear()
    await callback.message.edit_text(
        "Выберите действие:",
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
    logging.warning(f"--- Сработал УНИВЕРСАЛЬНЫЙ хэндлер неправильного ввода ---")
    logging.warning(f"Пользователь {message.from_user.id} прислал некорректный тип данных в состоянии {current_state}")
    
    await message.reply(
        "Я ожидаю файл определённого типа для выбранной операции.\n\n"
        "Пожалуйста, отправьте нужный файл или начните заново с команды /start."
    )
    logging.warning("--- Универсальный хэндлер завершен ---")