# Telegram Video Converter Bot

Production-ready Telegram bot to compress and convert large video files (up to 2GB native via Pyrogram Bot Token). Built with Python, Pyrogram, and FFmpeg.

## Features
- Handles up to 2GB videos natively
- Automatically detects video resolution and generates lower quality options
- Customizable file names and thumbnails (Auto/Custom)
- Real-time progress updates with ETA for Download, FFmpeg, and Upload
- Queue system to prevent RAM/CPU overload
- Disk space checking
- Allowed users whitelist for security

## Requirements
- Python 3.11+
- FFmpeg installed in system
- Telegram API ID and HASH from [my.telegram.org](https://my.telegram.org)
- Bot Token from [@BotFather](https://t.me/BotFather)

## Installation

### Local Setup
1. Clone the repository
2. Install FFmpeg (`sudo apt install ffmpeg` on Ubuntu)
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill the variables 
5. Run the bot: `python -m app.bot`

### Docker Setup
1. Copy `.env.example` to `.env` and configure variables.
2. Run: `docker-compose up -d --build`

### Google Colab Instructions
```python
# 1. Update and install FFmpeg
!apt-get update -qq
!apt-get install -y ffmpeg

# 2. Clone repository (or upload files)
# !git clone [https://github.com/your/repo.git](https://github.com/your/repo.git)
# %cd repo

# 3. Install packages
!pip install -r requirements.txt

# 4. Create .env file manually in Colab or write via code:
with open(".env", "w") as f:
    f.write("BOT_TOKEN=YOUR_TOKEN\nAPI_ID=YOUR_API_ID\nAPI_HASH=YOUR_API_HASH\nALLOWED_USERS=YOUR_ID\nMAX_CONCURRENT_CONVERSIONS=1")

# 5. Run the bot
!python -m app.bot