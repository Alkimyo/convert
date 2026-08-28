from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.jobs import user_jobs

@Client.on_callback_query(filters.regex(r"^q_(.*)"))
async def select_quality(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_jobs:
        return await callback.answer("Jarayon topilmadi yoki eskirgan.", show_alert=True)
        
    quality = callback.matches[0].group(1)
    user_jobs[user_id].quality = quality
    user_jobs[user_id].status = "filename_selection"
    
    await callback.message.edit_text(
        f"Tanlangan sifat: {quality}\n\n📁 Fayl nomini qanday saqlaymiz?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Default nom", callback_data="fname_default")],
            [InlineKeyboardButton("✏️ Nomini o'zgartirish", callback_data="fname_custom")]
        ])
    )