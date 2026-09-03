import asyncio
import logging
import os
import app.config
from pyrogram.types import ChatPrivileges
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
            user_client = client.user_client
            bot_me = await client.get_me()
            
            status_msg = await job.message.reply_text("⬇️ Yuklanish tayyorlanmoqda...")
            job.status = "downloading"
            
            # --- DUMP KANAL ---
            target_chat_id = app.config.DUMP_CHAT_ID
            try:
                if not target_chat_id: raise ValueError("ID yo'q")
                await user_client.get_chat(target_chat_id)
            except Exception:
                new_channel = await user_client.create_channel("Video Dump", "Bot bazasi")
                target_chat_id = new_channel.id
                await user_client.promote_chat_member(
                    chat_id=target_chat_id, user_id=bot_me.id, privileges=ChatPrivileges(can_post_messages=True)
                )
                app.config.DUMP_CHAT_ID = target_chat_id

            job_dir = DOWNLOAD_DIR / job.job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            input_path = job_dir / "input.mp4"
            out_dir = OUTPUT_DIR / job.job_id
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = out_dir / (job.custom_filename or "video.mp4")
            
            # --- YUKLAB OLISH LOGIKASI ---
            if job.video_url:
                await status_msg.edit_text("⬇️ Veb-saytdan yuklanmoqda (yt-dlp)...")
                import yt_dlp
                def download_video():
                    ydl_opts = {'outtmpl': str(input_path), 'format': 'best', 'quiet': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([job.video_url])
                await asyncio.to_thread(download_video)
                
            elif job.tg_chat_id and job.tg_message_id:
                # 🌟 HIMOYA QILINGAN KANALLAR UCHUN TO'G'RIDAN-TO'G'RI YUKLASH 🌟
                # (Bu yerda copy_message umuman ishlatilmaydi!)
                source_msg = await user_client.get_messages(job.tg_chat_id, job.tg_message_id)
                tracker = ProgressTracker(status_msg, "⬇️ Himoyalangan chatdan to'g'ridan-to'g'ri yuklanmoqda...")
                await user_client.download_media(source_msg, file_name=str(input_path), progress=tracker.update)
                
            else:
                # TO'G'RIDAN TO'G'RI BOTGA TASHLANGAN VIDEOLAR
                dump_in_msg = await client.copy_message(
                    chat_id=target_chat_id, from_chat_id=job.message.chat.id, message_id=job.message.id
                )
                user_in_msg = await user_client.get_messages(target_chat_id, dump_in_msg.id)
                tracker = ProgressTracker(status_msg, "⬇️ Telegramdan tezkor yuklanmoqda...")
                await user_client.download_media(user_in_msg, file_name=str(input_path), progress=tracker.update)
            
            if job.status == "cancelled": raise Exception("Bekor qilindi")

            await status_msg.edit_text("📊 Analyzing...")
            meta = await get_video_metadata(str(input_path))
            has_audio = meta['has_audio']
            
            if not job.duration or job.duration == 0:
                job.duration = meta['duration']
            
            user_thumb = await get_user_thumbnail(job.user_id)
            if user_thumb and os.path.exists(user_thumb): job.thumbnail = user_thumb
            else: job.thumbnail = await generate_auto_thumbnail(str(input_path), meta['duration'], job.job_id)
            
            if job.status == "cancelled": raise Exception("Bekor qilindi")
                
            job.status = "converting"
            success = await convert_video(job, str(input_path), str(output_path), status_msg, has_audio)
            
            if not success and job.status != "cancelled": raise Exception("FFmpeg xatosi")
            elif job.status == "cancelled": raise Exception("Bekor qilindi")
                
            job.status = "uploading"
            up_tracker = ProgressTracker(status_msg, "📤 Telegram serveriga yuklanmoqda...")
            
            width, height = 1280, 720
            if job.quality == "480p": width, height = 854, 480
            elif job.quality == "360p": width, height = 640, 360
            elif job.quality == "240p": width, height = 426, 240
            elif job.quality == "144p": width, height = 256, 144
            
            caption_text = f"🎬 {job.custom_filename or 'video'}\n📺 Quality: {job.quality}\n⏱ Duration: {int(job.duration//60):02d}:{int(job.duration%60):02d}"
            
            dump_out_msg = await user_client.send_video(
                chat_id=target_chat_id, video=str(output_path), caption=caption_text,
                thumb=job.thumbnail, width=width, height=height,
                duration=int(job.duration), progress=up_tracker.update
            )
            
            await status_msg.edit_text("🔄 Tayyor video yo'naltirilmoqda...")
            await client.copy_message(chat_id=job.user_id, from_chat_id=target_chat_id, message_id=dump_out_msg.id)
            await status_msg.delete()
            job.status = "completed"
            
        except Exception as e:
            if str(e) == "Bekor qilindi" or job.status == "cancelled": pass
            else: logger.error(f"Job failed: {e}", exc_info=True)
            try: await status_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")
            except: pass
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
