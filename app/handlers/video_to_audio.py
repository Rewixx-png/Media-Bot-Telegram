# app/handlers/video_to_audio.py

import os
import tempfile
import logging
import shutil

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from app.states.conversion import ConversionStates
from app.keyboards.inline import get_video_to_audio_formats_menu
from app.utils.ffmpeg_utils import extract_and_convert_audio
from config import LOCAL_API_PATH

router = Router()

@router.callback_query(F.data == "extract_audio_from_video_menu")
async def ask_for_audio_format(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_caption(
        caption="🎬 ➡ 🎵 <b>Режим: Видео в Аудио</b>\n\nВ какой формат сохранить звук?",
        reply_markup=get_video_to_audio_formats_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("v2a_format_"))
async def ask_for_video_file(callback: types.CallbackQuery, state: FSMContext):
    target_format = callback.data.split("_")[-1]
    await state.update_data(target_format=target_format)
    await state.set_state(ConversionStates.waiting_for_video_for_audio_extraction)
    await callback.message.edit_caption(caption=f"📂 Формат: <b>{target_format.upper()}</b>. Отправьте видео.")
    await callback.answer()

@router.message(ConversionStates.waiting_for_video_for_audio_extraction, F.video)
async def handle_video_for_audio_extraction(message: types.Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    target_format = user_data.get('target_format')
    await state.clear()

    status_msg = await message.reply("📥 Забираю файл...")

    try:
        file_info = await bot.get_file(message.video.file_id)
        relative_path = file_info.file_path.replace("/var/lib/telegram-bot-api/", "")
        host_path = os.path.join(LOCAL_API_PATH, relative_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, 'input_video')
            output_path = os.path.join(temp_dir, f"output.{target_format}")

            if os.path.exists(host_path):
                shutil.copy(host_path, input_path)
            else:
                await status_msg.edit_text("❌ Файл не найден.")
                return

            await status_msg.edit_text("⚙️ Извлекаю...")
            success = await extract_and_convert_audio(input_path, output_path, target_format)

            if success:
                await status_msg.edit_text("📤 Отправляю...")
                if target_format == 'ogg': await message.reply_voice(FSInputFile(output_path))
                elif target_format == 'mp3': await message.reply_audio(FSInputFile(output_path))
                else: await message.reply_document(FSInputFile(output_path))
                await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Ошибка извлечения.")

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        await status_msg.edit_text("❌ Ошибка.")