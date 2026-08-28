import asyncio
import json

async def get_video_metadata(filepath: str) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", filepath
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()
    data = json.loads(stdout)
    
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    has_audio = any(s.get("codec_type") == "audio" for s in data.get("streams", []))
    
    if not video_stream:
        raise ValueError("Video stream topilmadi.")
        
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    
    # Handle rotation metadata
    tags = video_stream.get("tags", {})
    rotation = tags.get("rotate")
    if rotation in ["90", "270", "-90"]:
        width, height = height, width

    duration = float(data.get("format", {}).get("duration", 0))
    
    return {
        "width": width,
        "height": height,
        "duration": duration,
        "has_audio": has_audio
    }