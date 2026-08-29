
import asyncio
import time
from app.core.jobs import Job
from pyrogram.types import Message

QUALITY_SETTINGS = {
    "720p": {"crf": "25", "maxrate": "1500k", "bufsize": "3000k", "audio": "96k", "height": 720},
    "540p": {"crf": "25", "maxrate": "1000k", "bufsize": "2000k", "audio": "64k", "height": 540},
    "480p": {"crf": "26", "maxrate": "800k",  "bufsize": "1600k", "audio": "64k", "height": 480},
    "360p": {"crf": "26", "maxrate": "500k",  "bufsize": "1000k", "audio": "48k", "height": 360},
    "240p": {"crf": "28", "maxrate": "300k",  "bufsize": "600k",  "audio": "32k", "height": 240},
    "144p": {"crf": "30", "maxrate": "150k",  "bufsize": "300k",  "audio": "24k", "height": 144},
}

async def convert_video(job: Job, input_path: str, output_path: str, status_msg: Message, has_audio: bool) -> bool:
    settings = QUALITY_SETTINGS[job.quality]
    
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", 
        "-preset", "ultrafast",
        "-tune", "fastdecode",
        "-threads", "0",
        "-crf", settings["crf"],
        "-maxrate", settings["maxrate"],
        "-bufsize", settings["bufsize"],
        "-vf", f"scale=-2:{settings['height']}:flags=fast_bilinear,fps=24", 
        "-movflags", "+faststart",
        "-progress", "pipe:1"
    ]
    
    if has_audio:
        cmd.extend(["-c:a", "aac", "-b:a", settings["audio"], "-ac", "2"])
    else:
        cmd.extend(["-an"])
        
    cmd.append(output_path)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    job.process = process

    duration_secs = float(job.duration) if job.duration else 0.0
    start_time = time.time()
    last_update = 0

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        
        line_str = line.decode('utf-8', errors='ignore').strip()
        
        if line_str.startswith("out_time_ms="):
            try:
                ms_str = line_str.split("=")[1]
                # FFmpeg ba'zan "N/A" qaytarishi mumkin, shuning uchun raqam ekanligini tekshiramiz
                if ms_str.lstrip('-').isdigit():
                    ms = int(ms_str)
                    current_sec = ms / 1_000_000
                    now = time.time()
                    
                    if now - last_update > 3:
                        last_update = now
                        percent = (current_sec / duration_secs) * 100 if duration_secs > 0 else 0
                        percent = max(0.0, min(percent, 100.0))
                        
                        elapsed = now - start_time
                        speed = current_sec / elapsed if elapsed > 0 else 0
                        eta = (duration_secs - current_sec) / speed if speed > 0 else 0
                        eta = max(0, eta)
                        eta_m, eta_s = divmod(int(eta), 60)
                        
                        bar_length = 16
                        filled = int(percent / (100 / bar_length))
                        bar = "█" * filled + "░" * (bar_length - filled)
                        
                        text = (
                            f"⚡ Tezkor Rejim ({job.quality})\n"
                            f"{bar} {percent:.1f}%\n"
                            f"⏱ Qolgan vaqt: {eta_m:02d}:{eta_s:02d}"
                        )
                        try:
                            # Html parse paramsiz yuboramiz, xato bermaydi
                            await status_msg.edit_text(text)
                        except Exception:
                            pass
            except Exception:
                pass

    await process.wait()
    return process.returncode == 0
