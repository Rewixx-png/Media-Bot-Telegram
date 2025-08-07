from aiogram.fsm.state import State, StatesGroup

class ConversionStates(StatesGroup):
    waiting_for_media_for_circle = State()
    waiting_for_audio_for_conversion = State()
    # НОВОЕ СОСТОЯНИЕ
    waiting_for_video_for_audio_extraction = State()