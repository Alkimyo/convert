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
@Client.on_message((filters.video | filters.document) & filters.private, group=-1)
async def handle_video(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in ALLOWED_USERS: raise StopPropagation
    
    media = message.video or message.document
    if message.document and "video" not in (message.document.mime_type or ""):
        # Agar bu umuman video bo'lmagan boshqa fayl bo'lsa
        raise StopPropagation

    if user_id in user_jobs: 
        await message.reply_text("⏳ Faol video mavjud.")
        raise StopPropagation

    width = getattr(media, "width", 1280) or 1280
    height = getattr(media, "height", 720) or 720
    duration = getattr(media, "duration", 0) or 0
    max_dim = max(width, height)
    orig_name = getattr(media, "file_name", "video.mp4") or "video.mp4"
    orig_quality_str = next((q[0] for q in QUALITIES if max_dim >= q[1] - 100), "Unknown")

    job = Job(user_id, message, media.file_id, orig_name, media.file_size, width, height, duration)
    user_jobs[user_id] = job

    text = f"🎬 Video qabul qilindi\n📝 {orig_name[:30]}\n📐 Res: {width}×{height}\n🎞 Orig: {orig_quality_str}\n\n⬇️ Sifatni tanlang:"
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
            
            # VIDEO YOKI HUJJAT (DOCUMENT) EKANLIGINI TEKSHIRISH
            media = None
            if tg_msg:
                if tg_msg.video:
                    media = tg_msg.video
                elif tg_msg.document and "video" in (tg_msg.document.mime_type or ""):
                    media = tg_msg.document
            
            if not media:
                await status_msg.edit_text("❌ Ushbu linkda video yoki MP4 fayl topilmadi!")
                raise StopPropagation
                
            width = getattr(media, "width", 1280) or 1280
            height = getattr(media, "height", 720) or 720
            duration = getattr(media, "duration", 0) or 0
            max_dim = max(width, height)
            orig_name = getattr(media, "file_name", "tg_video.mp4") or "tg_video.mp4"
            file_size = media.file_size
            orig_quality_str = next((q[0] for q in QUALITIES if max_dim >= q[1] - 100), "Unknown")
            
            job = Job(user_id, message, media.file_id, orig_name, file_size, width, height, duration, tg_chat_id=chat_id, tg_message_id=msg_id)
            user_jobs[user_id] = job
            
            text = f"🔗 Telegram Video topildi\n📝 Nomi: {orig_name[:40]}\n📐 Res: {width}×{height}\n🎞 Orig: {orig_quality_str}\n\n⬇️ Sifatni tanlang:"
            await status_msg.delete()
            await message.reply_text(text, reply_markup=get_inline_keyboard(max_dim))
            
        except StopPropagation:
            raise  # Qulfni xato sifatida ushlab qolmasligi uchun uni o'tkazib yuboramiz
        except Exception as e:
            await status_msg.edit_text(f"❌ Xatolik! Bu linkdagi video mavjud emas yoki User Session u bot/kanalni ko'ra olmaydi.\n(Xato: {type(e).__name__})")
            
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

            text = f"🔗 Veb Video topildi\n📝 Nomi: {orig_name[:40]}\n📐 Res: {width}×{height}\n🎞 Orig: {orig_quality_str}\n\n⬇️ Sifatni tanlang:"
            await status_msg.delete()
            await message.reply_text(text, reply_markup=get_inline_keyboard(max_dim))
        except StopPropagation:
            raise
        except Exception as e:
            await status_msg.edit_text("❌ Linkni o'qib bo'lmadi yoki video format qo'llab-quvvatlanmaydi.")
            
    raise StopPropagation
