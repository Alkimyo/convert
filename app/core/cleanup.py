import shutil
from app.config import DOWNLOAD_DIR, OUTPUT_DIR, TEMP_DIR
from app.core.jobs import Job

def cleanup_job_files(job: Job):
    paths = [
        DOWNLOAD_DIR / job.job_id,
        OUTPUT_DIR / job.job_id,
        TEMP_DIR / job.job_id
    ]
    for p in paths:
        if p.exists() and p.is_dir():
            shutil.rmtree(p, ignore_errors=True)