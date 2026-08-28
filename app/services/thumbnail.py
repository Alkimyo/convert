import asyncio
from pathlib import Path
from app.config import TEMP_DIR

async def generate_auto_thumbnail(video_path: str, duration: float, job_id: str) -> str:
    temp_dir = TEMP_DIR / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = temp_dir / "thumb.jpg"
    
    time_pos = duration * 0.1
    cmd = [
        "ffmpeg", "-y", "-ss", str(time_pos), "-i", video_path,
        "-vframes", "1", "-q:v", "2", str(thumb_path)
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    if thumb_path.exists():
        return str(thumb_path)
    return None