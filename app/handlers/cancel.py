from pyrogram import Client, filters
from pyrogram.types import Message
from app.config import ALLOWED_USERS
from app.core.jobs import user_jobs
from app.core.cleanup import cleanup_job_files

@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in ALLOWED_USERS:
        return
        
    if user_id in user_jobs:
        job = user_jobs[user_id]
        job.status = "cancelled"
        
        if job.process:
            try:
                job.process.terminate()
            except:
                pass
                
        cleanup_job_files(job)
        del user_jobs[user_id]
        await message.reply_text("🛑 Jarayon bekor qilindi.")
    else:
        await message.reply_text("Sizda faol jarayon yo'q.")