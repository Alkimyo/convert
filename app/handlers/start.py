from pyrogram import Client, filters, StopPropagation
from pyrogram.types import Message
from pyrogram.enums import ParseMode  # <-- Xatoni to'g'irlaydigan modul
from app.config import ALLOWED_USERS

@Client.on_message(filters.command("start") & filters.private, group=-1)
async def start_cmd(client: Client, message: Message):
    if message.from_user.id not in ALLOWED_USERS:
        await message.reply_text("❌ Sizga ruxsat yo'q.")
        raise StopPropagation
        
    await message.reply_text(
        "👋 Assalomu alaykum!\n\n"
        "Menga istalgan video yuboring yoki video linkini (Telegram/YouTube/Insta) tashlang, "
        "men uni o'lchamini kichraytirib va sifatini sozlab beraman."
    )
    raise StopPropagation

@Client.on_message(filters.command("help") & filters.private, group=-1)
async def help_cmd(client: Client, message: Message):
    if message.from_user.id not in ALLOWED_USERS:
        await message.reply_text("❌ Sizga ruxsat yo'q.")
        raise StopPropagation
        
    text = (
        "**🛠 Botdan foydalanish bo'yicha yordam:**\n\n"
        "1️⃣ **Video yuborish:** To'g'ridan-to'g'ri MP4 video yuboring.\n"
        "2️⃣ **Telegram Link:** Istalgan kanal, guruh yoki botdagi video linkini yuboring (Masalan: `t.me/kanal/123`).\n"
        "3️⃣ **Veb Link:** YouTube, Instagram Reels yoki ochiq MP4 linklarni yuboring.\n\n"
        "⚡️ *Barcha jarayonlar maksimal tezlikda (User Session orqali) bajariladi!*"
    )
    
    # "markdown" o'rniga ParseMode.MARKDOWN ishlatiladi!
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    raise StopPropagation

@Client.on_message(filters.command("id") & filters.private,group=-1)
async def id_cmd(client: Client, message: Message):
    await message.reply_text(f"Sizning ID: `{message.from_user.id}`")
