import asyncio
import re
import time
from app.core.jobs import Job
from pyrogram.types import Message

QUALITY_SETTINGS = {
    "720p": {"crf": "22", "maxrate": "2500k", "bufsize": "5000k", "audio": "128k", "height": 720},
    "540p": {"crf": "22", "maxrate": "1800k", "bufsize": "3600k", "audio": "96k", "height": 540},
    "480p": {"crf": "23", "maxrate": "1400k", "bufsize": "2800k", "audio": "96k", "height": 480},
    "360p": {"crf": "23", "maxrate": "900k", "bufsize": "1800k", "audio": "64k", "height": 360},
    "240p": {"crf": "24", "maxrate": "500k", "bufsize": "1000k", "audio": "48k", "height": 240},
    "144p": {"crf": "25", "maxrate": "250k", "bufsize": "500k", "audio": "32k", "height": 144},
}

async def convert_video(job: Job, input_path: str, output_path: str, status_msg: Message, has_audio: bool) -> bool:
    settings = QUALITY_SETTINGS[job.quality]
    
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", "-preset", "medium",
        "-crf", settings["crf"],
        "-maxrate", settings["maxrate"],
        "-bufsize", settings["bufsize"],
        "-vf", f"scale=-2:{settings['height']}",
        "-movflags", "+faststart",
        "-progress", "pipe:1"
    ]
    
    if has_audio:
        cmd.extend(["-c:a", "aac", "-b:a", settings["audio"]])
    else:
        cmd.extend(["-an"])
        
    cmd.append(output_path)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    job.process = process

    duration_secs = job.duration
    start_time = time.time()
    last_update = 0

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        
        line_str = line.decode('utf-8').strip()
        if "out_time_ms=" in line_str:
            try:
                ms = int(line_str.split("=")[1])
                current_sec = ms / 1_000_000
                now = time.time()
                
                if now - last_update > 3:
                    last_update = now
                    percent = (current_sec / duration_secs) * 100 if duration_secs else 0
                    percent = min(percent, 100)
                    
                    elapsed = now - start_time
                    speed = current_sec / elapsed if elapsed > 0 else 0
                    eta = (duration_secs - current_sec) / speed if speed > 0 else 0
                    eta_m, eta_s = divmod(int(eta), 60)
                    
                    bar_length = 16
                    filled = int(percent / (100 / bar_length))
                    bar = "█" * filled + "░" * (bar_length - filled)
                    
                    text = (
                        f"⚙️ {job.quality} tayyorlanmoqda...\n"
                        f"{bar} {percent:.1f}%\n"
                        f"⏱ ETA: {eta_m:02d}:{eta_s:02d}"
                    )
                    try:
                        await status_msg.edit_text(text)
                    except Exception:
                        pass
            except Exception:
                pass

    await process.wait()
    return process.returncode == 0