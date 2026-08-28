from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.jobs import user_jobs
from app.core.queue import job_queue
from app.utils.security import sanitize_filename
import os

@Client.on_callback_query(filters.regex(r"^fname_(.*)"))
async def select_filename_type(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_jobs:
        return await callback.answer("Jarayon topilmadi.", show_alert=True)
        
    choice = callback.matches[0].group(1)
    job = user_jobs[user_id]
    
    if choice == "default":
        name, ext = os.path.splitext(job.original_filename)
        job.custom_filename = sanitize_filename(f"{name} {job.quality}.mp4")
        job.status = "queued"
        await callback.message.edit_text("⏳ Navbatga qo'shildi.")
        await job_queue.put(job)
    elif choice == "custom":
        job.status = "waiting_custom_name"
        await callback.message.edit_text("✏️ Yangi fayl nomini yuboring.")

@Client.on_message(filters.text & filters.private)
async def receive_custom_name(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in user_jobs and user_jobs[user_id].status == "waiting_custom_name":
        job = user_jobs[user_id]
        safe_name = sanitize_filename(message.text)
        job.custom_filename = safe_name
        
        await message.reply_text(
            f"📁 Fayl nomi:\n{safe_name}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Tasdiqlash", callback_data="fname_confirm")],
                [InlineKeyboardButton("✏️ Qayta yozish", callback_data="fname_custom")]
            ])
        )

@Client.on_callback_query(filters.regex(r"^fname_confirm$"))
async def confirm_custom_name(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_jobs and user_jobs[user_id].status == "waiting_custom_name":
        job = user_jobs[user_id]
        job.status = "queued"
        await callback.message.edit_text("⏳ Navbatga qo'shildi.")
        await job_queue.put(job)
