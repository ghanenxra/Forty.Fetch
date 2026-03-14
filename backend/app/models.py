from __future__ import annotations

from pydantic import BaseModel, Field


class StartDownloadRequest(BaseModel):
    url: str = Field(min_length=5)
    quality: str = Field(default="1080p 60fps")


class StartDownloadResponse(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    speed: str
    eta: str
    message: str
    file_name: str | None = None
