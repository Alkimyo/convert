import shutil

def check_disk_space(required_bytes: int, path: str) -> bool:
    total, used, free = shutil.disk_usage(path)
    return free > required_bytes