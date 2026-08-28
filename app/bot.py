import asyncio
import logging
from pyrogram import Client, idle
from app.config import BOT_TOKEN, API_ID, API_HASH, USER_SESSION
from app.database import init_db
from app.core.queue import worker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    await init_db()
    
    # 1. Bot Client (Foydalanuvchi bilan gaplashish uchun)
    bot_client = Client(
        "video_converter_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
    
    # 2. User Client (Katta videolarni yuklash uchun)
    user_client = Client(
        "user_uploader",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=USER_SESSION
    )
    
    # Global o'zgaruvchi qilib qo'yamiz, queue'da ishlatish uchun
    bot_client.user_client = user_client
    
    await bot_client.start()
    await user_client.start()
    
    logger.info("Bot va User Client muvaffaqiyatli ishga tushdi!")
    
    asyncio.create_task(worker())
    await idle()
    
    await bot_client.stop()
    await user_client.stop()

if __name__ == "__main__":
    asyncio.run(main())
