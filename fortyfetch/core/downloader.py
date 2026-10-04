from fortyfetch.core.common import *
import customtkinter as ctk
import threading
import os
import time
import json
import traceback
import subprocess
import re
import shutil
import webbrowser
from tkinter import filedialog, messagebox

class DownloaderMixin:
        def _resolve_ffmpeg_location(self) -> str | None:
            if os.path.exists(self.ffmpeg_exe) and os.path.exists(self.ffprobe_exe):
                return self.assets_dir
            fallback = shutil.which("ffmpeg")
            if fallback:
                return os.path.dirname(fallback)
            return None

        def _update_download_progress(self, percent: float) -> None:
            p_val = max(0.0, min(100.0, percent))
            self.progress_bar.set(p_val / 100)
            self.percent_label.configure(text=f"{int(p_val)}%")
            self.circular_progress.set_progress(p_val)
            self.speed_label.configure(text="Downloading setup files...")

        def progress_hook(self, data: dict) -> None:
            status = data.get("status")
            if status == "downloading":
                p_str = data.get("_percent_str", "0%").replace("%", "").strip()
                speed = data.get("_speed_str", "Waiting...")
                eta = data.get("_eta_str", "")
                try:
                    clean_p_str = re.sub(r'\x1b\[[0-9;]*m', '', p_str)
                    match = re.search(r'\d+\.\d+|\d+', clean_p_str)
                    p_val = float(match.group(0)) if match else 0.0
                    p_val = max(0.0, min(100.0, p_val))
                except Exception:
                    p_val = 0.0

                # Throttle UI updates to ~10 FPS (every 100ms) to prevent GUI thread stutter
                now = time.perf_counter()
                if now - self._last_progress_time < 0.1 and p_val < 100.0:
                    return
                self._last_progress_time = now

                eta_text = f" • ETA {eta}" if eta else ""

                def _update():
                    self.progress_bar.set(p_val / 100)
                    self.percent_label.configure(text=f"{int(p_val)}%")
                    self.circular_progress.set_progress(p_val)
                    self.speed_label.configure(text=f"Speed: {speed}{eta_text}")
                    self.status_label.configure(text="Downloading stream...", text_color=ACCENT_CYAN)

                self.after(0, _update)

            elif status == "finished":
                self.after(0, lambda: self.status_label.configure(text="Merging streams with FFmpeg...", text_color=ACCENT_CYAN))

        def start_download_thread(self) -> None:
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showwarning("FortyFetch", "Please paste a YouTube video link.")
                return

            if not self.save_path:
                messagebox.showwarning("FortyFetch", "Please select a save folder.")
                return

            if not self.ffmpeg_location:
                messagebox.showerror("FortyFetch", "FFmpeg not available. Ensure ffmpeg.exe and ffprobe.exe are present in assets.")
                return

            self.download_btn.configure(state="disabled", text="FETCHING DATA...", fg_color=PANEL_ELEVATED)
            self.status_label.configure(text="Fetching video information...", text_color=ACCENT_CYAN)
            self.progress_bar.set(0)
            self.percent_label.configure(text="0%")
            self.circular_progress.set_progress(0)
            self.speed_label.configure(text="Establishing stream connection...")

            choice = self.selected_quality.get()
            threading.Thread(target=self.download_video, args=(url, choice), daemon=True).start()

        def _format_for_quality(self, choice: str) -> tuple[str, bool]:
            if "MP3" in choice or "Audio" in choice:
                return "bestaudio/best", True

            match = re.search(r"(\d+)p", choice)
            height = match.group(1) if match else "1080"

            if "60fps" in choice:
                fmt = (
                    f"bestvideo[height<={height}][fps<=60]+bestaudio/"
                    f"best[height<={height}][fps<=60]/best"
                )
            else:
                fmt = (
                    f"bestvideo[height<={height}]+bestaudio/"
                    f"best[height<={height}]/best"
                )
            return fmt, False

        def download_video(self, url: str, choice: str) -> None:
            # Lazy import of yt_dlp on background worker thread (zero startup impact)
            import yt_dlp

            fmt, is_mp3 = self._format_for_quality(choice)
            max_conns = int(self.settings.get("max_connections", 5))

            ydl_opts: dict = {
                "progress_hooks": [self.progress_hook],
                "outtmpl": os.path.join(self.save_path, "%(title).180B [%(id)s].%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "ffmpeg_location": self.ffmpeg_location,
                "format": fmt,
                "merge_output_format": "mp4",
                "nocheckcertificate": True,
                "retries": 10,
                "fragment_retries": 10,
                "concurrent_fragment_downloads": max_conns,
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
                    info = ydl.extract_info(url, download=True)
                    title = info.get("title", "YouTube Download") if isinstance(info, dict) else "YouTube Download"

                def _success():
                    self.status_label.configure(text="Completed ✓", text_color=ACCENT_GREEN)
                    self.progress_bar.set(1.0)
                    self.percent_label.configure(text="100%")
                    self.circular_progress.set_progress(100)
                    self.speed_label.configure(text=f"Saved to: {os.path.basename(self.save_path)}")

                    # Add to history
                    item = {
                        "title": title,
                        "format": choice,
                        "status": "Completed ✓",
                        "progress": 1.0,
                        "date": time.strftime("%H:%M:%S")
                    }
                    self.downloads_history.insert(0, item)
                    self._render_download_card(item)

                    messagebox.showinfo("FortyFetch", f"Download completed successfully!\n\n{title}")

                self.after(0, _success)
            except Exception as exc:
                traceback.print_exc()
                error_msg = str(exc)[:220]

                def _error():
                    self.status_label.configure(text="Failed ✕", text_color="#FF6B6B")
                    self.speed_label.configure(text="Download encountered an error")
                    messagebox.showerror("FortyFetch", f"Error:\n{error_msg}")

                self.after(0, _error)
            finally:
                self.after(0, self._reset_after_download)

        def _reset_after_download(self) -> None:
            self.download_btn.configure(state="normal", text="⬇   START FETCH", fg_color=ACCENT_CYAN)

