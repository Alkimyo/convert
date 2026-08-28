import asyncio
import logging
import signal
from pyrogram import Client
from app.config import BOT_TOKEN, API_ID, API_HASH, USER_SESSION
from app.database import init_db
from app.core.queue import worker

# 1-MUHIM TUZATISH: Bot xabarlarga javob berishi uchun handlerlar import qilinishi shart!
from app.handlers import start, video, quality, filename, thumbnail, cancel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    await init_db()
    
    # Bot va User clientlarni sozlash
    bot_client = Client(
        "video_converter_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
    
    user_client = Client(
        "user_uploader",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=USER_SESSION
    )
    
    bot_client.user_client = user_client
    
    await bot_client.start()
    await user_client.start()
    
    logger.info("Bot va User Client muvaffaqiyatli ishga tushdi!")
    
    asyncio.create_task(worker())
    
    # 2-MUHIM TUZATISH: pyrogram.idle() o'rniga xavfsiz (xatolik bermaydigan) kutish usuli
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass
            
    try:
        await stop_event.wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        logger.info("Bot to'xtatilmoqda...")
        await bot_client.stop()
        await user_client.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

