import aiosqlite
from pathlib import Path
from app.config import BASE_DIR

DB_PATH = BASE_DIR / "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                thumbnail_path TEXT
            )
        """)
        await db.commit()

async def get_user_thumbnail(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT thumbnail_path FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_user_thumbnail(user_id: int, path: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO users (user_id, thumbnail_path) VALUES (?, ?)", (user_id, path))
        await db.commit()

async def delete_user_thumbnail(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET thumbnail_path = NULL WHERE user_id = ?", (user_id,))
        await db.commit()