import re

def sanitize_filename(filename: str) -> str:
    """Fayl nomidan xavfli belgilarni olib tashlash va xavfsiz holatga keltirish."""
    if not filename:
        return "video.mp4"
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    filename = filename.strip()
    if not filename.lower().endswith(".mp4"):
        filename += ".mp4"
    return filename