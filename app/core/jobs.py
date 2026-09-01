import time
from typing import Optional
from pyrogram.types import Message

class Job:
    def __init__(self, user_id: int, message: Message, input_file_id: str,
                 original_filename: str, file_size: int, original_width: int,
                 original_height: int, duration: int, video_url: str = None,
                 tg_chat_id = None, tg_message_id = None):
        self.job_id = f"{int(time.time())}_{user_id}"
        self.user_id = user_id
        self.message = message
        self.input_file_id = input_file_id
        self.original_filename = original_filename
        self.file_size = file_size
        self.original_width = original_width
        self.original_height = original_height
        self.duration = duration
        self.video_url = video_url
        
        # TELEGRAM LINKLAR UCHUN YANGI QATORLAR
        self.tg_chat_id = tg_chat_id
        self.tg_message_id = tg_message_id
        
        self.quality: Optional[str] = None
        self.custom_filename: Optional[str] = None
        self.status = "pending"
        self.process = None
        self.thumbnail: Optional[str] = None

user_jobs = {}
