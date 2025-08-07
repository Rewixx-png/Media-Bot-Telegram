# app/handlers/video_to_audio.py

import os
import tempfile
import logging
import shutil  # <--- ДОБАВЛЕН ИМПОРТ

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest

from app.states.conversion import ConversionStates
from app.keyboards.inline import get_video_to_audio_formats_menu
from app.utils.ffmpeg_utils import extract_and_convert_audio

router = Router()

@router.callback_query(F.data == "extract_audio_from_video_menu")
async def ask_for_audio_format(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Выберите формат, в который нужно извлечь аудио из видео:",
        reply_markup=get_video_to_audio_formats_menu()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("v2a_format_"))
async def ask_for_video_file(callback: types.CallbackQuery, state: FSMContext):
    target_format = callback.data.split("_")[-1]
    await state.update_data(
        target_format=target_format,
        instruction_message_id=callback.message.message_id
    )
    await state.set_state(ConversionStates.waiting_for_video_for_audio_extraction)
    await callback.message.edit_text(f"Хорошо, извлекаем аудио в .{target_format}.\nТеперь отправьте мне видеофайл.")
    await callback.answer()

@router.message(ConversionStates.waiting_for_video_for_audio_extraction, F.video)
async def handle_video_for_audio_extraction(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    target_format = user_data.get('target_format')
    instruction_message_id = user_data.get('instruction_message_id')
    await state.clear()
    
    processing_message = await message.reply("Начинаю извлечение аудио... 🎧")
    
    try:
        file_info = await bot.get_file(message.video.file_id)
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, 'input_video')
            output_path = os.path.join(temp_dir, f"output.{target_format}")
            
            # --- ИСПРАВЛЕНИЕ: Копируем файл локально вместо скачивания ---
            shutil.copy(file_info.file_path, input_path)
            
            success = await extract_and_convert_audio(input_path, output_path, target_format)
            
            if success:
                if target_format == 'ogg':
                    await message.reply_voice(FSInputFile(output_path))
                elif target_format == 'mp3':
                    await message.reply_audio(FSInputFile(output_path))
                else: # wav
                    await message.reply_document(FSInputFile(output_path))
            else:
                await processing_message.edit_text("Не удалось извлечь аудио. Возможно, в видео нет звуковой дорожки. 😥")
                return
                
            await bot.delete_message(message.chat.id, processing_message.message_id)
            if instruction_message_id:
                try:
                    await bot.delete_message(message.chat.id, instruction_message_id)
                except TelegramBadRequest:
                    pass
                    
    except Exception as e:
        await processing_message.edit_text("Произошла неизвестная ошибка. 😔")
        logging.error(f"Error extracting audio from video: {e}", exc_info=True)