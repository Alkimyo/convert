import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.config import ALLOWED_USERS
from app.core.jobs import Job, user_jobs
from app.utils.disk import check_disk_space

logger = logging.getLogger(__name__)

QUALITIES = [
    ("1440p", 1440), ("1080p", 1080), ("720p", 720),
    ("540p", 540), ("480p", 480), ("360p", 360),
    ("240p", 240), ("144p", 144)
]

@Client.on_message(filters.video & filters.private)
async def handle_video(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in ALLOWED_USERS:
        return await message.reply_text("❌ Sizga ushbu botdan foydalanishga ruxsat berilmagan.")
        
    if user_id in user_jobs:
        return await message.reply_text("⏳ Sizda allaqachon faol video mavjud.")

    file_size = message.video.file_size
    if not check_disk_space(file_size * 2, "."):
        return await message.reply_text("❌ Serverda video uchun yetarli bo'sh joy mavjud emas.")

    width = message.video.width
    height = message.video.height
    max_dim = max(width, height)
    duration = message.video.duration
    orig_name = message.video.file_name or "video.mp4"
    
    # Originalni aniqlash
    orig_quality_str = "Unknown"
    for q_name, q_val in QUALITIES:
        if max_dim >= q_val - 100: # Threshold for odd resolutions
            orig_quality_str = q_name
            break

    available_qualities = [q for q in QUALITIES if q[1] < max_dim - 50]

    job = Job(
        user_id=user_id,
        message=message,
        input_file_id=message.video.file_id,
        original_filename=orig_name,
        file_size=file_size,
        original_width=width,
        original_height=height,
        duration=duration
    )
    user_jobs[user_id] = job

    text = (
        "🎬 Video qabul qilindi\n"
        f"📐 Resolution: {width}×{height}\n"
        f"🎞 Original: {orig_quality_str}\n"
        f"💾 Size: {file_size / (1024*1024):.2f} MB\n"
        f"⏱ Duration: {int(duration//60):02d}:{int(duration%60):02d}\n\n"
        "⬇️ Sifatni tanlang:"
    )

    if not available_qualities:
        del user_jobs[user_id]
        return await message.reply_text("❌ Ushbu videoni pasaytirish uchun boshqa sifat mavjud emas.")

    buttons = []
    for q_name, _ in available_qualities:
        icon = "📺" if int(q_name.replace("p", "")) >= 480 else "📱"
        buttons.append([InlineKeyboardButton(f"{icon} {q_name}", callback_data=f"q_{q_name}")])

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))