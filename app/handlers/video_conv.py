# app/handlers/video_conv.py

import os
import tempfile
import logging
import shutil

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from app.states.conversion import ConversionStates
from app.utils.ffmpeg_utils import convert_to_circle
from config import LOCAL_API_PATH

router = Router()

@router.callback_query(F.data == "convert_to_circle")
async def ask_for_circle_media(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ConversionStates.waiting_for_media_for_circle)
    # Запоминаем ID сообщения с меню, чтобы потом удалить/изменить
    await state.update_data(instruction_message_id=callback.message.message_id)
    
    await callback.message.edit_caption(
        caption="🎥 <b>Режим: Кружочек</b>\n\nОтправьте мне видео (MP4/MOV) или GIF.\nЯ обрежу его в квадрат и сделаю видеосообщение.", 
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(ConversionStates.waiting_for_media_for_circle, F.video | F.animation)
async def handle_video_for_circle(message: types.Message, state: FSMContext, bot: Bot):
    await state.clear()
    status_msg = await message.reply("📥 Ищу файл на сервере...")

    file_id = message.video.file_id if message.video else message.animation.file_id

    try:
        file_info = await bot.get_file(file_id)
        
        # Подмена пути
        docker_path = file_info.file_path
        relative_path = docker_path.replace("/var/lib/telegram-bot-api/", "")
        host_path = os.path.join(LOCAL_API_PATH, relative_path)
        
        logging.info(f"Processing: {host_path}")

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, 'input_file')
            output_path = os.path.join(temp_dir, 'output_video.mp4')

            if os.path.exists(host_path):
                shutil.copy(host_path, input_path)
            else:
                await status_msg.edit_text(f"❌ Файл не найден: {host_path}")
                return

            await status_msg.edit_text("⚙️ Магия FFmpeg...")
            success = await convert_to_circle(input_path, output_path)

            if success:
                await status_msg.edit_text("📤 Загружаю кружочек...")
                await message.reply_video_note(FSInputFile(output_path))
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Ошибка обработки видео.")

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Критическая ошибка.")