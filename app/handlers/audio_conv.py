# app/handlers/audio_conv.py

import os
import tempfile
import logging
import shutil

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message
from aiogram.exceptions import TelegramBadRequest

from app.states.conversion import ConversionStates
from app.keyboards.inline import get_audio_formats_menu, get_wav_config_menu, get_main_menu
from app.utils.ffmpeg_utils import convert_audio

router = Router()

# Списки опций для настройки WAV
WAV_BIT_DEPTHS = [16, 24, 8]
WAV_SAMPLE_RATES = [44100, 48000, 96000, 22050]


def _get_next_in_cycle(current_value, options_list):
    """Вспомогательная функция для циклического перебора списка."""
    try:
        current_index = options_list.index(current_value)
        next_index = (current_index + 1) % len(options_list)
        return options_list[next_index]
    except (ValueError, IndexError):
        return options_list[0]


@router.callback_query(F.data == "convert_audio_menu")
async def ask_for_audio_format(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_caption(
        caption="Выберите формат для конвертации аудиофайла:",
        reply_markup=get_audio_formats_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "audio_format_ogg")
async def ask_for_ogg_file(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(
        target_format='ogg',
        instruction_message_id=callback.message.message_id
    )
    await state.set_state(ConversionStates.waiting_for_audio_for_conversion)
    await callback.message.edit_caption(caption="Хорошо, конвертируем в .ogg.\nТеперь отправьте мне аудиофайл.")
    await callback.answer()


@router.callback_query(F.data == "audio_format_wav")
async def start_wav_config(callback: types.CallbackQuery, state: FSMContext):
    default_config = {
        'bit_depth': WAV_BIT_DEPTHS[0],
        'sample_rate': WAV_SAMPLE_RATES[0],
        'channels': 2
    }
    await state.update_data(wav_config=default_config)
    await callback.message.edit_caption(
        caption="Настройте параметры для WAV-файла:",
        reply_markup=get_wav_config_menu(default_config)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("wav_config_"))
async def process_wav_config(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "wav_config_done":
        await state.update_data(target_format='wav', instruction_message_id=callback.message.message_id)
        await state.set_state(ConversionStates.waiting_for_audio_for_conversion)
        await callback.message.edit_caption(caption="Отлично! Настройки сохранены.\nТеперь отправьте мне аудиофайл для конвертации.")
        await callback.answer()
        return

    user_data = await state.get_data()
    config = user_data.get('wav_config')
    if config is None:
        await callback.answer("Произошла ошибка состояния. Пожалуйста, начните заново.", show_alert=True)
        await state.clear()
        await callback.message.delete()
        await callback.message.answer("Пожалуйста, начните заново.", reply_markup=get_main_menu())
        return

    action = callback.data.replace("wav_config_", "")
    if action == 'bit_depth':
        config['bit_depth'] = _get_next_in_cycle(config['bit_depth'], WAV_BIT_DEPTHS)
    elif action == 'sample_rate':
        config['sample_rate'] = _get_next_in_cycle(config['sample_rate'], WAV_SAMPLE_RATES)
    elif action == 'channels':
        config['channels'] = 1 if config['channels'] == 2 else 2

    await state.update_data(wav_config=config)
    try:
        await callback.message.edit_caption(caption="Настройте параметры для WAV-файла:", reply_markup=get_wav_config_menu(config))
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.message(ConversionStates.waiting_for_audio_for_conversion, F.audio)
async def handle_audio_for_conversion(message: Message, state: FSMContext, bot: Bot):
    user_data = await state.get_data()
    target_format = user_data.get('target_format')
    wav_config = user_data.get('wav_config')
    instruction_message_id = user_data.get('instruction_message_id')
    await state.clear()

    processing_message = await message.reply("Конвертирую аудио... 🎶")

    try:
        file_info = await bot.get_file(message.audio.file_id)
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input_audio")
            output_path = os.path.join(temp_dir, f"output.{target_format}")

            shutil.copy(file_info.file_path, input_path)

            success = await convert_audio(input_path, output_path, target_format, config=wav_config)

            if success:
                if target_format == 'ogg':
                    await message.reply_voice(FSInputFile(output_path))
                else:
                    await message.reply_document(FSInputFile(output_path))
            else:
                await processing_message.edit_text("Не удалось конвертировать аудио. 😥")
                return

            await bot.delete_message(message.chat.id, processing_message.message_id)
            if instruction_message_id:
                try:
                    await bot.delete_message(message.chat.id, instruction_message_id)
                except TelegramBadRequest:
                    pass
    except Exception as e:
        await processing_message.edit_text("Произошла неизвестная ошибка. 😔")
        logging.error(f"Error processing audio for conversion: {e}", exc_info=True)