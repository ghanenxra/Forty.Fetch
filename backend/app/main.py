from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.models import JobStatusResponse, StartDownloadRequest, StartDownloadResponse
from app.services.download_manager import DownloadManager

BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = os.getenv("FORTYFETCH_DOWNLOAD_DIR", str(BASE_DIR / "downloads"))
FFMPEG_LOCATION = os.getenv("FORTYFETCH_FFMPEG_LOCATION")

manager = DownloadManager(output_dir=DOWNLOAD_DIR, ffmpeg_location=FFMPEG_LOCATION)
app = FastAPI(title="FortyFetch API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/downloads", response_model=StartDownloadResponse)
def start_download(payload: StartDownloadRequest) -> StartDownloadResponse:
    job_id = manager.start(url=payload.url, quality=payload.quality)
    return StartDownloadResponse(job_id=job_id)


@app.get("/downloads/{job_id}", response_model=JobStatusResponse)
def get_download(job_id: str) -> JobStatusResponse:
    job = manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        speed=job.speed,
        eta=job.eta,
        message=job.message,
        file_name=job.file_name,
    )


@app.get("/downloads/{job_id}/file")
def get_file(job_id: str) -> FileResponse:
    path = manager.resolve_file_path(job_id)
    if not path:
        raise HTTPException(status_code=404, detail="File not available")
    return FileResponse(path=path, filename=os.path.basename(path), media_type="application/octet-stream")
