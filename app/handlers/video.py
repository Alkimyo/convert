
           %%writefile app/handlers/video.py
import logging
import asyncio
from pyrogram import Client, filters, StopPropagation
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.config import ALLOWED_USERS
from app.core.jobs import Job, user_jobs

logger = logging.getLogger(__name__)

QUALITIES = [
    ("1440p", 1440), ("1080p", 1080), ("720p", 720),
    ("540p", 540), ("480p", 480), ("360p", 360),
    ("240p", 240), ("144p", 144)
]

def get_inline_keyboard(max_dim):
    available_qualities = [q for q in QUALITIES if q[1] < max_dim - 50]
    buttons = [[InlineKeyboardButton("✨ Original sifat (Juda tez)", callback_data="q_original")]]
    for q_name, _ in available_qualities:
        icon = "📺" if int(q_name.replace("p", "")) >= 480 else "📱"
        buttons.append([InlineKeyboardButton(f"{icon} {q_name}", callback_data=f"q_{q_name}")])
    return InlineKeyboardMarkup(buttons)

# VIDEO QABUL QILISH (-1 GURUH)
@Client.on_message(filters.video & filters.private, group=-1)
async def handle_video(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in ALLOWED_USERS: raise StopPropagation
    if user_id in user_jobs: 
        await message.reply_text("⏳ Faol video mavjud.")
        raise StopPropagation

    width, height = message.video.width, message.video.height
    duration, max_dim = message.video.duration, max(width, height)
    orig_name = message.video.file_name or "video.mp4"
    orig_quality_str = next((q[0] for q in QUALITIES if max_dim >= q[1] - 100), "Unknown")

    job = Job(user_id, message, message.video.file_id, orig_name, message.video.file_size, width, height, duration)
    user_jobs[user_id] = job

    text = f"🎬 Video qabul qilindi\n📐 Res: {width}×{height}\n🎞 Orig: {orig_quality_str}\n⏱ Dur: {int(duration//60):02d}:{int(duration%60):02d}\n\n⬇️ Sifatni tanlang:"
    await message.reply_text(text, reply_markup=get_inline_keyboard(max_dim))
    raise StopPropagation

# LINK QABUL QILISH (-1 GURUH)
@Client.on_message(filters.text & filters.private & filters.regex(r"https?://"), group=-1)
async def handle_link(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in ALLOWED_USERS: raise StopPropagation
    if user_id in user_jobs: 
        await message.reply_text("⏳ Faol video mavjud.")
        raise StopPropagation

    url = message.text.strip()
    
    # TELEGRAM LINK
    if "t.me/" in url or "telegram.me/" in url:
        status_msg = await message.reply_text("🔍 Telegram xabar tekshirilmoqda...")
        try:
            url_clean = url.split("?")[0].strip("/")
            parts = [p for p in url_clean.split("/") if p]
            msg_id = int(parts[-1])
            
            if "c" in parts:
                chat_id = int(f"-100{parts[parts.index('c') + 1]}")
            else:
                chat_id = parts[-2]
            
            user_client = client.user_client
            tg_msg = await user_client.get_messages(chat_id, msg_id)
            
            if not tg_msg or not tg_msg.video:
                await status_msg.edit_text("❌ Ushbu linkda video topilmadi!")
                raise StopPropagation
                
            video = tg_msg.video
            width, height, duration = video.width, video.height, video.duration
            max_dim = max(width, height)
            orig_name = video.file_name or "tg_video.mp4"
            file_size = video.file_size
            orig_quality_str = next((q[0] for q in QUALITIES if max_dim >= q[1] - 100), "Unknown")
            
            job = Job(user_id, message, video.file_id, orig_name, file_size, width, height, duration, tg_chat_id=chat_id, tg_message_id=msg_id)
            user_jobs[user_id] = job
            
            text = f"🔗 Telegram Video topildi\n📝 Nomi: {orig_name[:40]}\n📐 Res: {width}×{height}\n🎞 Orig: {orig_quality_str}\n⏱ Dur: {int(duration//60):02d}:{int(duration%60):02d}\n\n⬇️ Sifatni tanlang:"
            await status_msg.delete()
            await message.reply_text(text, reply_markup=get_inline_keyboard(max_dim))
        except Exception as e:
            await status_msg.edit_text(f"❌ Xatolik! Bu linkdagi video mavjud emas yoki ruxsat yo'q.\n({e})")
            
    # WEB LINK (YouTube, Insta, MP4)
    else:
        status_msg = await message.reply_text("🔗 Veb-link tahlil qilinmoqda...")
        try:
            import yt_dlp
            def extract():
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl: return ydl.extract_info(url, download=False)
            
            info = await asyncio.to_thread(extract)
            width, height = info.get('width') or 1280, info.get('height') or 720
            duration = info.get('duration') or 0
            orig_name = (info.get('title') or 'video') + ".mp4"
            file_size = info.get('filesize') or info.get('filesize_approx') or 0
            max_dim = max(width, height)
            orig_quality_str = next((q[0] for q in QUALITIES if max_dim >= q[1] - 100), "Unknown")

            job = Job(user_id, message, "url", orig_name, file_size, width, height, duration, video_url=url)
            user_jobs[user_id] = job

            text = f"🔗 Veb Video topildi\n📝 Nomi: {orig_name[:40]}\n📐 Res: {width}×{height}\n🎞 Orig: {orig_quality_str}\n⏱ Dur: {int(duration//60):02d}:{int(duration%60):02d}\n\n⬇️ Sifatni tanlang:"
            await status_msg.delete()
            await message.reply_text(text, reply_markup=get_inline_keyboard(max_dim))
        except Exception as e:
            await status_msg.edit_text("❌ Linkni o'qib bo'lmadi yoki video format qo'llab-quvvatlanmaydi.")
            
    raise StopPropagation
