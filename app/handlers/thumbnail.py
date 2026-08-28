import os
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.config import ALLOWED_USERS, THUMBNAIL_DIR
from app.database import get_user_thumbnail, set_user_thumbnail, delete_user_thumbnail

@Client.on_message(filters.photo & filters.private)
async def save_thumbnail(client: Client, message: Message):
    if message.from_user.id not in ALLOWED_USERS:
        return
        
    user_id = message.from_user.id
    path = THUMBNAIL_DIR / f"{user_id}.jpg"
    
    await message.download(file_name=str(path))
    await set_user_thumbnail(user_id, str(path))
    await message.reply_text("✅ Yangi thumbnail saqlandi!")

@Client.on_message(filters.command("thumbnail") & filters.private)
async def thumbnail_cmd(client: Client, message: Message):
    if message.from_user.id not in ALLOWED_USERS:
        return
        
    user_id = message.from_user.id
    thumb_path = await get_user_thumbnail(user_id)
    
    if thumb_path and os.path.exists(thumb_path):
        await message.reply_text(
            "🖼 Sizning thumbnailingiz mavjud.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁 Ko'rish", callback_data="thumb_view")],
                [InlineKeyboardButton("🗑 O'chirish", callback_data="thumb_del_ask")]
            ])
        )
    else:
        await message.reply_text("🖼 Thumbnail o'rnatilmagan.\nVideo yuborsangiz, videodan avtomatik thumbnail olinadi.")

@Client.on_callback_query(filters.regex(r"^thumb_(.*)"))
async def thumbnail_cb(client: Client, callback: CallbackQuery):
    action = callback.matches[0].group(1)
    user_id = callback.from_user.id
    thumb_path = await get_user_thumbnail(user_id)
    
    if action == "view":
        if thumb_path and os.path.exists(thumb_path):
            await callback.message.reply_photo(photo=thumb_path)
        await callback.answer()
        
    elif action == "del_ask":
        await callback.message.edit_text(
            "⚠️ Thumbnailni o'chirishni xohlaysizmi?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Ha, o'chirish", callback_data="thumb_del_yes")],
                [InlineKeyboardButton("❌ Bekor qilish", callback_data="thumb_del_no")]
            ])
        )
        
    elif action == "del_yes":
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
        await delete_user_thumbnail(user_id)
        await callback.message.edit_text("✅ Thumbnail o'chirildi.")
        
    elif action == "del_no":
        await callback.message.delete()