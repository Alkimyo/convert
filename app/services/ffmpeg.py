
import asyncio
import time
from app.core.jobs import Job
from pyrogram.types import Message

# YUQORI CRF (Kichik hajm) saqlab qolindi
QUALITY_SETTINGS = {
    "720p": {"crf": "27", "audio": "128k", "height": 720},
    "540p": {"crf": "28", "audio": "96k",  "height": 540},
    "480p": {"crf": "29", "audio": "96k",  "height": 480},
    "360p": {"crf": "30", "audio": "64k",  "height": 360},
    "240p": {"crf": "32", "audio": "48k",  "height": 240},
    "144p": {"crf": "34", "audio": "32k",  "height": 144},
}

async def convert_video(job: Job, input_path: str, output_path: str, status_msg: Message, has_audio: bool) -> bool:
    
    if job.quality == "original":
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-c", "copy",
            "-movflags", "+faststart",
            output_path
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        await status_msg.edit_text("⚡ Original format saqlanmoqda (Tezkor nusxalash)...")
        await process.wait()
        return process.returncode == 0

    settings = QUALITY_SETTINGS[job.quality]
    
    # 🚀 ENG MAKSIMAL TEZLIK SOZLAMALARI:
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", 
        "-preset", "ultrafast",       # 1. Eng tezkor rejim
        "-tune", "fastdecode",        # 2. Dekodlashni tezlashtirish
        "-profile:v", "baseline",     # 3. Eng yengil profil (B-framelarni o'chiradi, CPU ga nagruzka tushmaydi)
        "-threads", "0",              # Barcha CPU yadrolari
        "-crf", settings["crf"], 
        "-vf", f"scale=-2:{settings['height']}:flags=fast_bilinear", 
        "-pix_fmt", "yuv420p",        # Standart va tezkor rang formati
        "-movflags", "+faststart",
        "-progress", "pipe:1"
    ]
    
    if has_audio:
        # Ovozni oddiy stereo ga o'tkazib, tezlikni tejaymiz
        cmd.extend(["-c:a", "aac", "-b:a", settings["audio"], "-ac", "2"])
    else:
        cmd.extend(["-an"])
        
    cmd.append(output_path)

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    job.process = process

    duration_secs = float(job.duration) if job.duration else 0.0
    start_time = time.time()
    last_update = 0

    while True:
        line = await process.stdout.readline()
        if not line: break
        
        line_str = line.decode('utf-8', errors='ignore').strip()
        if line_str.startswith("out_time_ms="):
            try:
                ms_str = line_str.split("=")[1]
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
                        eta_m, eta_s = divmod(int(max(0, eta)), 60)
                        
                        bar_length = 16
                        filled = int(percent / (100 / bar_length))
                        bar = "█" * filled + "░" * (bar_length - filled)
                        
                        text = (
                            f"🚀 <b>Turbo Rejim ({job.quality})</b>\n"
                            f"{bar} {percent:.1f}%\n"
                            f"⏱ ETA: {eta_m:02d}:{eta_s:02d}"
                        )
                        try: await status_msg.edit_text(text, parse_mode="html")
                        except Exception: pass
            except Exception: pass

    await process.wait()
    return process.returncode == 0
