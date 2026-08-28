import asyncio
import logging
from pyrogram import Client
from app.config import BOT_TOKEN, API_ID, API_HASH
from app.database import init_db
from app.core.queue import worker
from app.handlers import start, video, quality, filename, thumbnail, cancel

logging.basicConfig(
    filename='logs/bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load handlers by simply keeping them imported
# Pyrogram will automatically register them since decorators are applied at load

async def main():
    await init_db()
    
    client = Client(
        "video_converter_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
    
    # Start background worker
    asyncio.create_task(worker())
    
    logger.info("Bot started successfully")
    await client.start()
    
    # Keep bot running
    import pyrogram
    await pyrogram.idle()
    
if __name__ == "__main__":
    # Ensure nested async loops work if any
    asyncio.run(main())