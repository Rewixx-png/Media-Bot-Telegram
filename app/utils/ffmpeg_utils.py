# app/utils/ffmpeg_utils.py

import asyncio
import logging

async def convert_to_circle(input_path: str, output_path: str) -> bool:
    """
    Конвертирует видео в кружок 360x360 с обрезкой.
    Возвращает True при успехе, иначе False.
    """
    video_side = 360
    command = [
        'ffmpeg', '-i', input_path, '-y',
        '-vf', f'scale={video_side}:{video_side}:force_original_aspect_ratio=increase,crop={video_side}:{video_side}',
        '-c:v', 'libx264', '-preset', 'ultrafast',
        # Убираем аудиодорожку, так как видеокружки в Telegram беззвучны
        '-an',
        output_path
    ]
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        logging.error(f"FFmpeg (circle) failed: {stderr.decode()}")
        return False
    return True

async def convert_audio(input_path: str, output_path: str, target_format: str, config: dict = None) -> bool:
    """
    Конвертирует аудиофайл в заданный формат.
    Для WAV может принимать словарь с настройками.
    """
    command = ['ffmpeg', '-i', input_path, '-y']

    if target_format == 'ogg':
        command.extend(['-c:a', 'libopus'])
    elif target_format == 'wav' and config:
        # ИЗМЕНЕНО: Добавлена логика выбора кодека для разной глубины бита
        if config['bit_depth'] == 8:
            codec = 'pcm_u8'  # 8-битный PCM - беззнаковый (unsigned)
        else:
            # 16- и 24-битный - знаковые (signed), с прямым порядком байтов (little-endian)
            codec = f"pcm_s{config['bit_depth']}le"
        
        sample_rate = str(config['sample_rate'])
        channels = str(config['channels'])
        command.extend(['-c:a', codec, '-ar', sample_rate, '-ac', channels])

    command.append(output_path)
    
    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        logging.error(f"FFmpeg (audio) failed: {stderr.decode()}")
        return False
    return True

async def extract_and_convert_audio(input_path: str, output_path: str, target_format: str) -> bool:
    """
    Извлекает аудиодорожку из видео и конвертирует в нужный формат.
    Возвращает True при успехе, иначе False.
    """
    command = [
        'ffmpeg', '-i', input_path, '-y',
        '-vn',  # Указывает FFmpeg игнорировать видео
    ]
    if target_format == 'ogg':
        # Для голосовых сообщений
        command.extend(['-c:a', 'libopus'])
    elif target_format == 'mp3':
        # Стандартное качество VBR (Variable Bitrate) для MP3
        command.extend(['-c:a', 'libmp3lame', '-q:a', '2'])
    elif target_format == 'wav':
        # Для WAV при извлечении можно оставить параметры по умолчанию
        # FFmpeg сам выберет стандартный кодек (pcm_s16le)
        pass # Дополнительных команд не требуется
    
    command.append(output_path)

    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        logging.error(f"FFmpeg (extract audio) failed: {stderr.decode()}")
        return False
    return True