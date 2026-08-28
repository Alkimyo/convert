import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")
ALLOWED_USERS = [int(u.strip()) for u in os.getenv("ALLOWED_USERS", "").split(",") if u.strip()]
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_CONVERSIONS", 1))

BASE_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE_DIR / os.getenv("DOWNLOAD_DIR", "downloads")
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "outputs")
THUMBNAIL_DIR = BASE_DIR / os.getenv("THUMBNAIL_DIR", "thumbnails")
TEMP_DIR = BASE_DIR / os.getenv("TEMP_DIR", "temp")
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
for d in [DOWNLOAD_DIR, OUTPUT_DIR, THUMBNAIL_DIR, TEMP_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)