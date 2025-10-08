# app/handlers/video_conv.py

import os
import tempfile
import logging
import shutil

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest

from app.states.conversion import ConversionStates
from app.utils.ffmpeg_utils import convert_to_circle

router = Router()

@router.callback_query(F.data == "convert_to_circle")
async def ask_for_circle_media(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ConversionStates.waiting_for_media_for_circle)
    await state.update_data(instruction_message_id=callback.message.message_id)
    # --- ИСПРАВЛЕНИЕ: Используем edit_caption ---
    await callback.message.edit_caption(caption="Отлично! Отправьте мне видео или GIF-анимацию.")
    await callback.answer()

@router.message(ConversionStates.waiting_for_media_for_circle, F.video | F.animation)
async def handle_video_for_circle(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    instruction_message_id = user_data.get('instruction_message_id')
    await state.clear()

    processing_message = await message.reply("Начинаю конвертацию... ⏳")

    file_id = message.video.file_id if message.video else message.animation.file_id

    try:
        file_info = await bot.get_file(file_id)
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, 'input_file')
            output_path = os.path.join(temp_dir, 'output_video.mp4')

            shutil.copy(file_info.file_path, input_path)

            success = await convert_to_circle(input_path, output_path)

            if success:
                await message.reply_video_note(FSInputFile(output_path))
            else:
                await processing_message.edit_text("Не удалось конвертировать видео. 😥")
                return

            await bot.delete_message(message.chat.id, processing_message.message_id)
            if instruction_message_id:
                try:
                    await bot.delete_message(message.chat.id, instruction_message_id)
                except TelegramBadRequest:
                    pass

    except Exception as e:
        await processing_message.edit_text("Произошла неизвестная ошибка. 😔")
        logging.error(f"Error processing video: {e}", exc_info=True)