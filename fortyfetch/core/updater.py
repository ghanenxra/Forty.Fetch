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

class UpdaterMixin:
        def check_bundled_tools(self) -> None:
            if self.ffmpeg_location:
                self.status_label.configure(text="Ready to Fetch", text_color=TEXT_PRIMARY)
            else:
                self.status_label.configure(text="FFmpeg not found", text_color="#FF6B6B")
                messagebox.showwarning(
                    "FortyFetch",
                    "FFmpeg/FFprobe not found in assets or system PATH. Downloads may fail.",
                )

        def start_manual_update_thread(self) -> None:
            self.status_label.configure(text="Checking for updates...", text_color=TEXT_PRIMARY)
            self.speed_label.configure(text="Connecting to GitHub release servers...")
            threading.Thread(target=self.check_and_update_dependencies, daemon=True).start()

        def check_and_update_dependencies(self) -> None:
            if is_frozen_build():
                try:
                    tag, download_url = self._fetch_latest_app_release_details()
                    if tag and download_url and self._is_version_newer(tag, APP_VERSION):
                        self.after(0, lambda: self.prompt_and_install_app_update(tag, download_url))
                        return
                except Exception:
                    traceback.print_exc()

            self._check_and_update_tools()

        def _fetch_latest_app_release_details(self) -> tuple[str | None, str | None]:
            try:
                from urllib import request as urlrequest
                req = urlrequest.Request(
                    "https://api.github.com/repos/ghanenxra/Forty.Fetch/releases/latest",
                    headers={"User-Agent": "FortyFetch/1.0"},
                )
                with urlrequest.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))

                tag = data.get("tag_name", "").strip().lstrip("vV")

                download_url = None
                for asset in data.get("assets", []):
                    name = asset.get("name", "")
                    if name.endswith(".exe") and "setup" not in name.lower():
                        download_url = asset.get("browser_download_url")
                        break

                if not download_url:
                    for asset in data.get("assets", []):
                        name = asset.get("name", "")
                        if name.endswith(".exe"):
                            download_url = asset.get("browser_download_url")
                            break

                return tag, download_url
            except Exception:
                traceback.print_exc()
                return None, None

        def prompt_and_install_app_update(self, tag: str, download_url: str) -> None:
            want_update = messagebox.askyesno(
                "FortyFetch Update",
                f"A new version of FortyFetch (v{tag}) is available.\n\n"
                "Would you like to download and install it now?\n"
                "The app will restart automatically after the update.",
            )
            if not want_update:
                self.status_label.configure(text="Checking tool updates...", text_color=TEXT_PRIMARY)
                threading.Thread(target=self._check_and_update_tools, daemon=True).start()
                return

            self.status_label.configure(text=f"Downloading FortyFetch v{tag}...", text_color=ACCENT_CYAN)
            self.progress_bar.set(0)
            self.percent_label.configure(text="0%")
            self.speed_label.configure(text="Connecting to download server...")

            def download_and_apply():
                try:
                    import tempfile
                    from urllib import request as urlrequest
                    temp_dir = tempfile.gettempdir()
                    temp_file_path = os.path.join(temp_dir, f"FortyFetch_manual_update_{tag}.exe")
                    req = urlrequest.Request(download_url, headers={"User-Agent": "FortyFetch/1.0"})
                    with urlrequest.urlopen(req, timeout=90) as resp:
                        total_size = int(resp.headers.get('content-length', 0))
                        downloaded = 0
                        block_size = 1024 * 64
                        with open(temp_file_path, "wb") as out:
                            while True:
                                block = resp.read(block_size)
                                if not block:
                                    break
                                out.write(block)
                                downloaded += len(block)
                                if total_size > 0:
                                    percent = (downloaded / total_size) * 100
                                    self.after(0, lambda p=percent: self._update_download_progress(p))

                    if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 1024 * 1024:
                        self.after(0, lambda: self._apply_manual_update_and_restart(temp_file_path))
                    else:
                        raise RuntimeError("Downloaded file is invalid or too small.")
                except Exception as exc:
                    traceback.print_exc()
                    error_msg = str(exc)[:220]
                    self.after(0, lambda: messagebox.showerror("FortyFetch Update", f"Update failed: {error_msg}"))
                    self.after(0, lambda: self.status_label.configure(text="Update failed", text_color="#FF6B6B"))
                    self.after(0, self._reset_after_download)
                    self.after(2000, lambda: threading.Thread(target=self._check_and_update_tools, daemon=True).start())

            threading.Thread(target=download_and_apply, daemon=True).start()

        def _apply_manual_update_and_restart(self, temp_file_path: str) -> None:
            current_exe = sys.executable
            powershell_cmd = f"Start-Sleep -Seconds 2; Copy-Item -Path '{temp_file_path}' -Destination '{current_exe}' -Force; Start-Process '{current_exe}'; Remove-Item -Path '{temp_file_path}'"
            try:
                subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", powershell_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
                self.destroy()
            except Exception as exc:
                traceback.print_exc()
                messagebox.showerror("FortyFetch Update", f"Failed to restart and apply update: {exc}")

        def _check_and_update_tools(self) -> None:
            updates_done: list[str] = []
            no_updates: list[str] = []
            warnings: list[str] = []

            try:
                ytdlp_result = self._manual_update_ytdlp()
                if ytdlp_result == "updated":
                    updates_done.append("yt-dlp")
                elif ytdlp_result == "no_update":
                    no_updates.append("yt-dlp")
                else:
                    warnings.append(ytdlp_result)

                ffmpeg_result = self._manual_update_bundled_ffmpeg()
                if ffmpeg_result == "updated":
                    updates_done.extend(["ffmpeg", "ffprobe"])
                elif ffmpeg_result == "no_update":
                    no_updates.extend(["ffmpeg", "ffprobe"])
                else:
                    warnings.append(ffmpeg_result)
            except Exception as exc:
                warnings.append(f"Update check failed: {str(exc)[:160]}")

            def _finish_ui() -> None:
                if updates_done:
                    self.status_label.configure(text="Update successful", text_color=ACCENT_CYAN)
                else:
                    self.status_label.configure(text="No updates available", text_color=ACCENT_CYAN)

                if updates_done:
                    self.speed_label.configure(text=f"Updated: {', '.join(updates_done)}")
                elif warnings:
                    self.speed_label.configure(text="No updates available")
                else:
                    self.speed_label.configure(text="Everything is up to date")

                lines: list[str] = []
                if updates_done:
                    lines.append(f"Updated successfully: {', '.join(updates_done)}")
                if no_updates:
                    lines.append(f"No updates available: {', '.join(no_updates)}")
                if warnings:
                    lines.extend([f"Note: {item}" for item in warnings])
                if not lines:
                    lines.append("No updates available.")
                messagebox.showinfo("FortyFetch Updates", "\n".join(lines))

            self.after(0, _finish_ui)

        def _manual_update_ytdlp(self) -> str:
            if is_frozen_build():
                try:
                    import yt_dlp.version
                    ytdlp_version = yt_dlp.version.__version__
                except Exception:
                    ytdlp_version = "unknown"
                latest = self._fetch_latest_ytdlp_version()
                if latest and self._is_version_newer(latest, ytdlp_version):
                    return (
                        f"yt-dlp update available ({latest}), but packaged build cannot auto-update yt-dlp."
                    )
                return "no_update"

            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                    capture_output=True,
                    text=True,
                    timeout=240,
                )
                output = (proc.stdout or "") + "\n" + (proc.stderr or "")
                low = output.lower()
                if proc.returncode == 0 and (
                    "successfully installed yt-dlp" in low or "uninstalling yt-dlp" in low
                ):
                    return "updated"
                if proc.returncode == 0 and "requirement already satisfied" in low:
                    return "no_update"
                if proc.returncode == 0 and "collecting yt-dlp" not in low:
                    return "no_update"
                if proc.returncode == 0:
                    return "updated"
                return f"yt-dlp update skipped: {output.strip()[:160]}"
            except Exception as exc:
                return f"yt-dlp update skipped: {str(exc)[:160]}"

        def _manual_update_bundled_ffmpeg(self) -> str:
            if not os.path.exists(self.ffmpeg_exe) or not os.path.exists(self.ffprobe_exe):
                return "FFmpeg/FFprobe not bundled in assets. Install them manually if needed."

            try:
                current_version = self._get_ffmpeg_version(self.ffmpeg_exe)
                latest_tag, zip_url = self._fetch_latest_ffmpeg_release()
                if not latest_tag or not zip_url:
                    return "Could not check FFmpeg update right now."

                if current_version and not self._is_version_newer(latest_tag, current_version):
                    return "no_update"

                import tempfile
                with tempfile.TemporaryDirectory() as tmp_dir:
                    zip_path = os.path.join(tmp_dir, "ffmpeg_latest.zip")
                    self._download_file(zip_url, zip_path)
                    ffmpeg_new, ffprobe_new = self._extract_ffmpeg_bins(zip_path, tmp_dir)
                    shutil.copy2(ffmpeg_new, self.ffmpeg_exe)
                    shutil.copy2(ffprobe_new, self.ffprobe_exe)

                self.ffmpeg_location = self.assets_dir
                return "updated"
            except Exception as exc:
                return f"FFmpeg/FFprobe update skipped: {str(exc)[:160]}"

        def _fetch_latest_ytdlp_version(self) -> str | None:
            try:
                from urllib import request as urlrequest
                req = urlrequest.Request(
                    "https://pypi.org/pypi/yt-dlp/json",
                    headers={"User-Agent": "FortyFetch/1.0"},
                )
                with urlrequest.urlopen(req, timeout=20) as resp:
                    payload = resp.read().decode("utf-8", errors="replace")
                match = re.search(r'"version"\s*:\s*"([^"]+)"', payload)
                return match.group(1) if match else None
            except Exception:
                return None

        def _fetch_latest_ffmpeg_release(self) -> tuple[str | None, str | None]:
            from urllib import request as urlrequest
            req = urlrequest.Request(
                "https://api.github.com/repos/GyanD/codexffmpeg/releases/latest",
                headers={"User-Agent": "FortyFetch/1.0"},
            )
            with urlrequest.urlopen(req, timeout=25) as resp:
                payload = resp.read().decode("utf-8", errors="replace")

            tag_match = re.search(r'"tag_name"\s*:\s*"([^"]+)"', payload)
            tag = tag_match.group(1).strip() if tag_match else None
            zip_match = re.search(
                r'"browser_download_url"\s*:\s*"([^"]*essentials_build\.zip)"',
                payload,
                flags=re.IGNORECASE,
            )
            zip_url = zip_match.group(1).replace("\\/", "/") if zip_match else None
            return tag, zip_url

        def _download_file(self, url: str, target_path: str) -> None:
            from urllib import request as urlrequest
            req = urlrequest.Request(url, headers={"User-Agent": "FortyFetch/1.0"})
            with urlrequest.urlopen(req, timeout=90) as resp, open(target_path, "wb") as out:
                shutil.copyfileobj(resp, out)

        def _extract_ffmpeg_bins(self, zip_path: str, extract_dir: str) -> tuple[str, str]:
            import zipfile
            ffmpeg_candidate = ""
            ffprobe_candidate = ""
            with zipfile.ZipFile(zip_path, "r") as zf:
                for name in zf.namelist():
                    lower_name = name.lower()
                    if lower_name.endswith("/bin/ffmpeg.exe") or lower_name.endswith("\\bin\\ffmpeg.exe"):
                        ffmpeg_candidate = name
                    elif lower_name.endswith("/bin/ffprobe.exe") or lower_name.endswith("\\bin\\ffprobe.exe"):
                        ffprobe_candidate = name

                if not ffmpeg_candidate or not ffprobe_candidate:
                    raise RuntimeError("Could not find ffmpeg.exe/ffprobe.exe in update package.")

                zf.extract(ffmpeg_candidate, path=extract_dir)
                zf.extract(ffprobe_candidate, path=extract_dir)

            ffmpeg_path = os.path.join(extract_dir, ffmpeg_candidate)
            ffprobe_path = os.path.join(extract_dir, ffprobe_candidate)
            return ffmpeg_path, ffprobe_path

        def _get_ffmpeg_version(self, ffmpeg_path: str) -> str:
            try:
                proc = subprocess.run(
                    [ffmpeg_path, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                first_line = (proc.stdout or "").splitlines()
                if not first_line:
                    return ""
                match = re.search(r"ffmpeg version\s+([^\s]+)", first_line[0], flags=re.IGNORECASE)
                if not match:
                    return ""
                token = match.group(1).lstrip("nN")
                return token.split("-")[0]
            except Exception:
                return ""

        def _is_version_newer(self, new_version: str, old_version: str) -> bool:
            def normalize(value: str) -> list[int]:
                nums = re.findall(r"\d+", value)
                return [int(n) for n in nums[:4]] if nums else [0]

            new_parts = normalize(new_version)
            old_parts = normalize(old_version)
            length = max(len(new_parts), len(old_parts))
            new_parts.extend([0] * (length - len(new_parts)))
            old_parts.extend([0] * (length - len(old_parts)))
            return new_parts > old_parts

