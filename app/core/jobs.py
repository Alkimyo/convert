import uuid
import time
from dataclasses import dataclass
from typing import Optional
from pyrogram.types import Message

@dataclass
class Job:
    user_id: int
    message: Message
    input_file_id: str
    original_filename: str
    file_size: int
    job_id: str = ""
    status: str = "waiting"
    original_width: int = 0
    original_height: int = 0
    duration: float = 0.0
    quality: str = ""
    custom_filename: str = ""
    thumbnail: Optional[str] = None
    process = None  # asyncio subprocess
    
    def __post_init__(self):
        if not self.job_id:
            self.job_id = uuid.uuid4().hex

# State management
user_jobs = {}  # user_id -> Job