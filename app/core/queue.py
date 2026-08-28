import asyncio
import logging
import os
from app.config import DOWNLOAD_DIR, OUTPUT_DIR, MAX_CONCURRENT
from app.core.jobs import user_jobs, Job
from app.core.cleanup import cleanup_job_files
from app.services.ffmpeg import convert_video
from app.services.ffprobe import get_video_metadata
from app.services.thumbnail import generate_auto_thumbnail
from app.database import get_user_thumbnail
from app.utils.progress import ProgressTracker

job_queue = asyncio.Queue()
semaphore = asyncio.Semaphore(MAX_CONCURRENT)
logger = logging.getLogger(__name__)

async def process_job(job: Job):
    async with semaphore:
        if job.status == "cancelled":
            cleanup_job_files(job)
            return

        try:
            client = job.message._client
            status_msg = await job.message.reply_text("⬇️ Yuklanmoqda...")
            job.status = "downloading"
            
            # Paths
            job_dir = DOWNLOAD_DIR / job.job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            input_path = job_dir / "input.mp4"
            
            out_dir = OUTPUT_DIR / job.job_id
            out_dir.mkdir(parents=True, exist_ok=True)
            output_filename = job.custom_filename
            output_path = out_dir / output_filename
            
            # Download
            tracker = ProgressTracker(status_msg, "⬇️ Yuklanmoqda...")
            await client.download_media(
                job.message,
                file_name=str(input_path),
                progress=tracker.update
            )
            
            if job.status == "cancelled":
                raise Exception("Bekor qilindi")

            # Meta
            await status_msg.edit_text("📊 Analyzing...")
            meta = await get_video_metadata(str(input_path))
            has_audio = meta['has_audio']
            
            # Thumbnail setup
            user_thumb = await get_user_thumbnail(job.user_id)
            if user_thumb and os.path.exists(user_thumb):
                job.thumbnail = user_thumb
            else:
                job.thumbnail = await generate_auto_thumbnail(str(input_path), meta['duration'], job.job_id)
            
            if job.status == "cancelled":
                raise Exception("Bekor qilindi")
                
            # Convert
            job.status = "converting"
            success = await convert_video(job, str(input_path), str(output_path), status_msg, has_audio)
            
            if not success and job.status != "cancelled":
                raise Exception("FFmpeg xatosi")
            elif job.status == "cancelled":
                raise Exception("Bekor qilindi")
                
            # Upload
            job.status = "uploading"
            up_tracker = ProgressTracker(status_msg, "📤 Serverga yuklanmoqda...")
            
            user_client = client.user_client  # bot.py da ulab qo'ygan edik
            
            width, height = 1280, 720
            if job.quality == "480p": width, height = 854, 480
            elif job.quality == "360p": width, height = 640, 360
            
            # 1. User akkaunt videoni yopiq Dump kanalga yuklaydi
            dump_message = await user_client.send_video(
                chat_id=DUMP_CHAT_ID,
                video=str(output_path),
                caption=f"🎬 {output_filename} | Sifat: {job.quality}",
                thumb=job.thumbnail,
                width=width,
                height=height,
                duration=int(job.duration),
                progress=up_tracker.update
            )
            
            await status_msg.edit_text("🔄 Videoni sizga yubormoqdamiz...")
            
            # 2. Bot videoni Dump kanaldan olib, foydalanuvchiga forward/copy qiladi
            caption_text = f"🎬 {output_filename}\n📺 Quality: {job.quality}\n⏱ Duration: {int(job.duration//60):02d}:{int(job.duration%60):02d}"
            
            await client.copy_message(
                chat_id=job.user_id,
                from_chat_id=DUMP_CHAT_ID,
                message_id=dump_message.id,
                caption=caption_text
            )
            
            await status_msg.delete()
            job.status = "completed"
            
        except Exception as e:
            if str(e) == "Bekor qilindi" or job.status == "cancelled":
                try:
                    await status_msg.edit_text("🛑 Jarayon bekor qilindi.")
                except:
                    pass
            else:
                logger.error(f"Job failed: {e}", exc_info=True)
                try:
                    await status_msg.edit_text("❌ Video konvertatsiyasida xatolik.")
                except:
                    pass
            job.status = "failed"
            
        finally:
            cleanup_job_files(job)
            if job.user_id in user_jobs:
                del user_jobs[job.user_id]

async def worker():
    while True:
        job = await job_queue.get()
        asyncio.create_task(process_job(job))
        job_queue.task_done()
