import time
from pyrogram.types import Message

class ProgressTracker:
    def __init__(self, message: Message, action_text: str):
        self.message = message
        self.action_text = action_text
        self.last_update_time = 0
        self.start_time = time.time()

    async def update(self, current: int, total: int):
        now = time.time()
        if now - self.last_update_time < 3 and current != total:
            return

        self.last_update_time = now
        percent = current * 100 / total if total else 0
        elapsed = now - self.start_time
        speed = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0

        bar_length = 16
        filled = int(percent / (100 / bar_length))
        bar = "█" * filled + "░" * (bar_length - filled)
        
        speed_mb = speed / (1024 * 1024)
        current_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        eta_m, eta_s = divmod(int(eta), 60)

        text = (
            f"{self.action_text}\n"
            f"{bar} {percent:.1f}%\n"
            f"💾 {current_mb:.1f} MB / {total_mb:.1f} MB\n"
            f"⚡ {speed_mb:.1f} MB/s\n"
            f"⏱ ETA: {eta_m:02d}:{eta_s:02d}"
        )
        try:
            await self.message.edit_text(text)
        except Exception:
            pass