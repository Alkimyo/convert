
from pyrogram import Client, filters
from pyrogram.exceptions import StopPropagation
from pyrogram.types import Message
from app.config import ALLOWED_USERS

@Client.on_message(filters.command("start") & filters.private, group=-1)
async def start_cmd(client: Client, message: Message):
    if message.from_user.id not in ALLOWED_USERS:
        await message.reply_text("❌ Sizga ruxsat yo'q.")
        raise StopPropagation
        
    await message.reply_text("👋 Assalomu alaykum!\n\nMenga istalgan video yuboring yoki video linkini (Telegram/YouTube) tashlang, men uni o'lchamini kichraytirib va sifatini sozlab beraman.")
    raise StopPropagation

@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client: Client, message: Message):
    if message.from_user.id not in ALLOWED_USERS:
        return
    text = (
        "🎬 *Video Converter Bot*\n\n"
        "1️⃣ Video yuboring\n"
        "2️⃣ Sifatni tanlang\n"
        "3️⃣ Fayl nomini tanlang\n"
        "4️⃣ FFmpeg videoni qayta ishlaydi\n"
        "5️⃣ Tayyor video Telegramga yuboriladi\n\n"
        "🖼 *Thumbnail:*\n"
        "Istalgan rasmni botga yuboring.\n\n"
        "Buyruqlar:\n"
        "/thumbnail — thumbnail boshqarish\n"
        "/cancel — jarayonni bekor qilish\n"
        "/id — Telegram ID"
    )
    await message.reply_text(text, parse_mode="markdown")

@Client.on_message(filters.command("id") & filters.private)
async def id_cmd(client: Client, message: Message):
    await message.reply_text(f"Sizning ID: `{message.from_user.id}`")
