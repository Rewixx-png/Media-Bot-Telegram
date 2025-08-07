from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру главного меню."""
    buttons = [
        [InlineKeyboardButton(text="📹 Сделать кружок", callback_data="convert_to_circle")],
        [InlineKeyboardButton(text="🎵 Конвертировать аудиофайл", callback_data="convert_audio_menu")],
        [InlineKeyboardButton(text="🎬 Извлечь аудио из видео", callback_data="extract_audio_from_video_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_audio_formats_menu() -> InlineKeyboardMarkup:
    """Клавиатура для конвертации АУДИОФАЙЛОВ (с кнопкой настройки)."""
    buttons = [
        [
            InlineKeyboardButton(text="🎙️ OGG (голосовое)", callback_data="audio_format_ogg"),
            InlineKeyboardButton(text="🎼 WAV (настроить)", callback_data="audio_format_wav"),
        ],
        [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_video_to_audio_formats_menu() -> InlineKeyboardMarkup:
    """Клавиатура для извлечения аудио ИЗ ВИДЕО."""
    buttons = [
        [
            InlineKeyboardButton(text="🎵 MP3", callback_data="v2a_format_mp3"),
            InlineKeyboardButton(text="🎙️ OGG", callback_data="v2a_format_ogg"),
            InlineKeyboardButton(text="🎼 WAV", callback_data="v2a_format_wav"),
        ],
        [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_wav_config_menu(config: dict) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для настройки параметров WAV.
    Принимает словарь с текущими настройками.
    """
    builder = InlineKeyboardBuilder()

    # Формируем текст для кнопок на основе текущей конфигурации
    bit_depth_text = f"Глубина бита: {config['bit_depth']}-bit"
    sample_rate_text = f"Частота: {int(config['sample_rate'] / 1000)} кГц"
    channels_text = f"Каналы: {'Моно' if config['channels'] == 1 else 'Стерео'}"

    # Добавляем кнопки для цикличного изменения каждого параметра
    builder.row(InlineKeyboardButton(text=bit_depth_text, callback_data="wav_config_bit_depth"))
    builder.row(InlineKeyboardButton(text=sample_rate_text, callback_data="wav_config_sample_rate"))
    builder.row(InlineKeyboardButton(text=channels_text, callback_data="wav_config_channels"))
    
    # Кнопка "Готово" для подтверждения и "Назад" для отмены настройки
    builder.row(
        InlineKeyboardButton(text="✅ Готово", callback_data="wav_config_done"),
        InlineKeyboardButton(text="« Назад", callback_data="convert_audio_menu")
    )
    return builder.as_markup()