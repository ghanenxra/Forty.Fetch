from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass
from typing import Any

import yt_dlp


QUALITY_TO_HEIGHT = {
    "360p 60fps": "360",
    "480p 60fps": "480",
    "720p 60fps": "720",
    "1080p 60fps": "1080",
    "1440p 60fps": "1440",
    "2160p 60fps (4K)": "2160",
    "4320p 60fps (8K)": "4320",
}


@dataclass
class DownloadJob:
    job_id: str
    url: str
    quality: str
    status: str = "queued"
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    message: str = "Waiting"
    file_name: str | None = None


class DownloadManager:
    def __init__(self, output_dir: str, ffmpeg_location: str | None = None) -> None:
        self.output_dir = output_dir
        self.ffmpeg_location = ffmpeg_location
        self._jobs: dict[str, DownloadJob] = {}
        self._lock = threading.Lock()
        os.makedirs(self.output_dir, exist_ok=True)

    def start(self, url: str, quality: str) -> str:
        job_id = str(uuid.uuid4())
        job = DownloadJob(job_id=job_id, url=url, quality=quality)
        with self._lock:
            self._jobs[job_id] = job

        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()
        return job_id

    def get(self, job_id: str) -> DownloadJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def resolve_file_path(self, job_id: str) -> str | None:
        job = self.get(job_id)
        if not job or not job.file_name:
            return None
        path = os.path.join(self.output_dir, job.file_name)
        return path if os.path.exists(path) else None

    def _run_job(self, job_id: str) -> None:
        job = self.get(job_id)
        if not job:
            return

        self._update(job_id, status="running", message="Preparing download")
        fmt, is_mp3 = self._format_for_quality(job.quality)

        def hook(data: dict[str, Any]) -> None:
            status = data.get("status", "")
            if status == "downloading":
                percent_text = str(data.get("_percent_str", "0")).replace("%", "").strip()
                try:
                    percent_val = max(0.0, min(100.0, float(percent_text)))
                except ValueError:
                    percent_val = 0.0
                self._update(
                    job_id,
                    progress=percent_val,
                    speed=str(data.get("_speed_str", "")),
                    eta=str(data.get("_eta_str", "")),
                    message="Downloading",
                )
            elif status == "finished":
                self._update(job_id, message="Finalizing media")

        ydl_opts: dict[str, Any] = {
            "noplaylist": True,
            "quiet": True,
            "format": fmt,
            "merge_output_format": "mp4",
            "ffmpeg_location": self.ffmpeg_location,
            "progress_hooks": [hook],
            "outtmpl": os.path.join(self.output_dir, "%(title).120B [%(id)s].%(ext)s"),
            "nocheckcertificate": True,
            "user_agent": (
                "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
            ),
            "referer": "https://www.youtube.com/",
        }

        if is_mp3:
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(job.url, download=True)

            final_name = self._resolve_output_name(info, is_mp3)
            self._update(
                job_id,
                status="completed",
                progress=100.0,
                file_name=final_name,
                message="Completed",
            )
        except Exception as exc:
            self._update(job_id, status="failed", message=str(exc)[:220])

    def _resolve_output_name(self, info: Any, is_mp3: bool) -> str | None:
        if not isinstance(info, dict):
            return None
        req = info.get("requested_downloads")
        if isinstance(req, list) and req:
            entry = req[0]
            path = entry.get("filepath") if isinstance(entry, dict) else None
            if isinstance(path, str):
                return os.path.basename(path)
        filename = info.get("_filename")
        if isinstance(filename, str):
            base, _ = os.path.splitext(filename)
            ext = ".mp3" if is_mp3 else ".mp4"
            return os.path.basename(base + ext)
        return None

    def _update(self, job_id: str, **kwargs: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for key, value in kwargs.items():
                setattr(job, key, value)

    @staticmethod
    def _format_for_quality(choice: str) -> tuple[str, bool]:
        if "MP3" in choice:
            return "bestaudio/best", True

        height = QUALITY_TO_HEIGHT.get(choice, "1080")
        fmt = (
            f"bestvideo[height<={height}][fps<=60]+bestaudio/"
            f"best[height<={height}][fps<=60]/best"
        )
        return fmt, False
