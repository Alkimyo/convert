import asyncio
import logging
import os
import app.config  # Dinamik xotira uchun
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
            status_msg = await job.message.reply_text("⬇️ Yuklanmoqda...")
            job.status = "downloading"

            job_dir = DOWNLOAD_DIR / job.job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            input_path = job_dir / "input.mp4"

            out_dir = OUTPUT_DIR / job.job_id
            out_dir.mkdir(parents=True, exist_ok=True)
            output_filename = job.custom_filename
            output_path = out_dir / output_filename

            tracker = ProgressTracker(status_msg, "⬇️ Yuklanmoqda...")
            await client.download_media(
                job.message,
                file_name=str(input_path),
                progress=tracker.update
            )

            if job.status == "cancelled": raise Exception("Bekor qilindi")

            await status_msg.edit_text("📊 Analyzing...")
            meta = await get_video_metadata(str(input_path))
            has_audio = meta['has_audio']

            user_thumb = await get_user_thumbnail(job.user_id)
            if user_thumb and os.path.exists(user_thumb):
                job.thumbnail = user_thumb
            else:
                job.thumbnail = await generate_auto_thumbnail(str(input_path), meta['duration'], job.job_id)

            if job.status == "cancelled": raise Exception("Bekor qilindi")

            job.status = "converting"
            success = await convert_video(job, str(input_path), str(output_path), status_msg, has_audio)

            if not success and job.status != "cancelled":
                raise Exception("FFmpeg xatosi")
            elif job.status == "cancelled":
                raise Exception("Bekor qilindi")

            # --- UPLOAD QISMI: AVTOMATIK KANAL VA BOT ORQALI YUBORISH ---
            job.status = "uploading"
            up_tracker = ProgressTracker(status_msg, "📤 Telegram serveriga yuklanmoqda...")

            user_client = client.user_client
            bot_me = await client.get_me()
            target_chat_id = app.config.DUMP_CHAT_ID

            # 1. Yashirin kanalni tekshiramiz yoki YANGI yaratamiz
            try:
                if not target_chat_id:
                    raise ValueError("ID yo'q")
                await user_client.get_chat(target_chat_id)
                await client.get_chat(target_chat_id) # Bot ham ko'ra olishini tekshiramiz
            except Exception as e:
                logger.warning(f"Kanal topilmadi, yangi baza yaratilmoqda... Xato: {e}")
                try:
                    # Sizning akkauntingiz orqali kanal yaratamiz
                    new_channel = await user_client.create_channel("Video Dump", "Bot bazasi")
                    target_chat_id = new_channel.id

                    # Botni shu kanalga Admin qilamiz
                    await user_client.promote_chat_member(
                        chat_id=target_chat_id,
                        user_id=bot_me.id,
                        privileges=ChatPrivileges(can_post_messages=True)
                    )

                    # ID ni keshda saqlab qolamiz (keyingi videolar uchun)
                    app.config.DUMP_CHAT_ID = target_chat_id
                    logger.info(f"✅ Yangi Dump Kanal yaratildi: {target_chat_id}")
                except Exception as create_err:
                    raise Exception(f"Kanal yaratishda xato: {create_err}")

            width, height = 1280, 720
            if job.quality == "480p": width, height = 854, 480
            elif job.quality == "360p": width, height = 640, 360

            caption_text = f"🎬 {output_filename}\n📺 Quality: {job.quality}\n⏱ Duration: {int(job.duration//60):02d}:{int(job.duration%60):02d}"

            # 2. Sizning akkauntingiz videoni Limit-siz yopiq kanalga yuklaydi
            dump_msg = await user_client.send_video(
                chat_id=target_chat_id,
                video=str(output_path),
                caption=caption_text,
                thumb=job.thumbnail,
                width=width,
                height=height,
                duration=int(job.duration),
                progress=up_tracker.update
            )

            await status_msg.edit_text("🔄 Tayyor video yo'naltirilmoqda...")

            # 3. Bot kanaldagi tayyor videoni foydalanuvchiga nusxalab (copy_message) beradi
            # copy_message bo'lgani uchun foydalanuvchi "Forwarded from..." yozuvini ko'rmaydi, to'ppa-to'g'ri BOTDAN keladi!
            await client.copy_message(
                chat_id=job.user_id,
                from_chat_id=target_chat_id,
                message_id=dump_msg.id
            )

            await status_msg.delete()
            job.status = "completed"

        except Exception as e:
            if str(e) == "Bekor qilindi" or job.status == "cancelled":
                try: await status_msg.edit_text("🛑 Jarayon bekor qilindi.")
                except: pass
            else:
                logger.error(f"Job failed: {e}", exc_info=True)
                try: await status_msg.edit_text("❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")
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
