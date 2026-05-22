import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import traceback
import webbrowser
import zipfile
from tkinter import filedialog, messagebox
from urllib import request as urlrequest

import customtkinter as ctk
import yt_dlp
from PIL import Image
from yt_dlp.version import __version__ as YTDLP_VERSION


ACCENT_COLOR = "#00D2FF"
ACCENT_HOVER = "#00A6CC"
BG_COLOR = "#080A0F"
CARD_COLOR = "#16181F"
INPUT_COLOR = "#06080D"
TEXT_MUTED = "#8D96A7"

APP_VERSION = "3.0.0"
APP_TITLE = f"FortyFetch v{APP_VERSION} - High Speed Youtube Downloader"
DISCORD_URL = "https://discord.com/users/1323161662739714120"
GITHUB_URL = "https://github.com/ghanenxra"
PAYPAL_URL = "https://www.paypal.com/paypalme/ghanenxra"
UPI_ID = "9024810096@fam"

QUALITY_OPTIONS = [
    "360p 60fps",
    "480p 60fps",
    "720p 60fps",
    "1080p 60fps",
    "1440p 60fps",
    "2160p 60fps (4K)",
    "4320p 60fps (8K)",
    "MP3 (Audio)",
]


def is_frozen_build() -> bool:
    return bool(getattr(sys, "frozen", False))


def should_exit_early_for_packaged_relaunch() -> bool:
    if not is_frozen_build():
        return False
    args = [arg.lower() for arg in sys.argv[1:]]
    return "-m" in args and "pip" in args


def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_path, relative_path)


class FortyFetchApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        self.title(APP_TITLE)
        self.geometry("860x620")
        self.minsize(780, 580)
        self.configure(fg_color=BG_COLOR)

        self.assets_dir = resource_path("assets")
        self.ffmpeg_exe = os.path.join(self.assets_dir, "ffmpeg.exe")
        self.ffprobe_exe = os.path.join(self.assets_dir, "ffprobe.exe")
        self.ffmpeg_location = self._resolve_ffmpeg_location()

        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.selected_quality = ctk.StringVar(value="1080p 60fps")

        self.pending_update_path = None
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        self._set_icon()
        self._build_ui()

        self.after(300, self.check_bundled_tools)
        if is_frozen_build():
            self.speed_label.configure(text="Bundled build mode")
            threading.Thread(target=self.check_app_update_silently, daemon=True).start()
        else:
            threading.Thread(target=self.check_and_update_ytdlp, daemon=True).start()

    def _set_icon(self) -> None:
        icon_path = os.path.join(self.assets_dir, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

    def _resolve_ffmpeg_location(self) -> str | None:
        if os.path.exists(self.ffmpeg_exe) and os.path.exists(self.ffprobe_exe):
            return self.assets_dir

        fallback = shutil.which("ffmpeg")
        if fallback:
            return os.path.dirname(fallback)
        return None

    def _build_ui(self) -> None:
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=38, pady=(10, 0))

        ctk.CTkButton(
            top_row,
            text="Check for Updates",
            width=170,
            height=34,
            corner_radius=10,
            fg_color="#1E7F5D",
            hover_color="#269B73",
            font=("Segoe UI", 12, "bold"),
            command=self.start_manual_update_thread,
        ).pack(side="right")

        ctk.CTkButton(
            top_row,
            text="Help",
            width=90,
            height=34,
            corner_radius=10,
            fg_color="#2A2F39",
            hover_color="#3A404A",
            font=("Segoe UI", 12, "bold"),
            command=self.show_update_help,
        ).pack(side="right", padx=(0, 10))

        ctk.CTkLabel(self, text="FORTY.FETCH", font=("Impact", 48), text_color=ACCENT_COLOR).pack(pady=(12, 0))
        ctk.CTkLabel(
            self,
            text="POWERED BY FORTY QUINN",
            font=("Segoe UI", 14, "bold"),
            text_color="#666B76",
        ).pack(pady=(0, 10))

        self.main_card = ctk.CTkFrame(
            self,
            fg_color=CARD_COLOR,
            corner_radius=20,
            border_width=1,
            border_color="#2B2E36",
        )
        self.main_card.pack(fill="both", expand=True, padx=38, pady=(6, 8))

        ctk.CTkLabel(
            self.main_card,
            text="PASTE YOUTUBE LINK",
            font=("Segoe UI", 13, "bold"),
            text_color=ACCENT_COLOR,
        ).pack(anchor="w", padx=24, pady=(16, 6))

        self.url_entry = ctk.CTkEntry(
            self.main_card,
            height=48,
            corner_radius=12,
            border_width=2,
            border_color="#2F323C",
            fg_color=INPUT_COLOR,
            text_color="#DCE6F9",
            placeholder_text="Paste YouTube link here...",
            placeholder_text_color="#7D8391",
            font=("Segoe UI", 13),
        )
        self.url_entry.pack(fill="x", padx=24, pady=(0, 14))

        option_row = ctk.CTkFrame(self.main_card, fg_color="transparent")
        option_row.pack(fill="x", padx=24, pady=(0, 8))

        self.quality_menu = ctk.CTkOptionMenu(
            option_row,
            variable=self.selected_quality,
            values=QUALITY_OPTIONS,
            width=190,
            height=42,
            corner_radius=10,
            fg_color="#232730",
            button_color=ACCENT_COLOR,
            button_hover_color=ACCENT_HOVER,
            font=("Segoe UI", 12),
            dropdown_font=("Segoe UI", 11),
        )
        self.quality_menu.pack(side="left", padx=(0, 14))

        self.folder_btn = ctk.CTkButton(
            option_row,
            text="SAVE FOLDER",
            height=42,
            corner_radius=10,
            fg_color="#232730",
            hover_color="#303643",
            text_color="#F0F4FB",
            font=("Segoe UI", 12),
            command=self.select_path,
        )
        self.folder_btn.pack(side="left", fill="x", expand=True)

        self.status_label = ctk.CTkLabel(
            self.main_card,
            text="Ready to Fetch",
            font=("Segoe UI", 14),
            text_color="#F5F9FF",
        )
        self.status_label.pack(pady=(10, 6))

        self.progress_bar = ctk.CTkProgressBar(
            self.main_card,
            height=12,
            corner_radius=8,
            fg_color="#070A0F",
            progress_color=ACCENT_COLOR,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=28, pady=(0, 6))

        progress_row = ctk.CTkFrame(self.main_card, fg_color="transparent")
        progress_row.pack(fill="x", padx=28, pady=(0, 10))
        self.percent_label = ctk.CTkLabel(
            progress_row,
            text="0%",
            font=("Segoe UI", 13, "bold"),
            text_color=ACCENT_COLOR,
        )
        self.percent_label.pack(side="left")

        self.speed_label = ctk.CTkLabel(
            progress_row,
            text="Waiting...",
            font=("Segoe UI", 12, "italic"),
            text_color="#9DA6BA",
        )
        self.speed_label.pack(side="right")

        self.download_btn = ctk.CTkButton(
            self,
            text="START FETCH",
            width=280,
            height=48,
            corner_radius=16,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color="#03131B",
            font=("Segoe UI", 18, "bold"),
            command=self.start_download_thread,
        )
        self.download_btn.pack(pady=(8, 10))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=38, pady=(0, 10))

        ctk.CTkButton(
            footer,
            text="Buy Me a Coffee",
            width=170,
            height=36,
            corner_radius=10,
            fg_color="#FF813F",
            hover_color="#FF985C",
            font=("Segoe UI", 12),
            command=self.show_donation_info,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            footer,
            text="Discord",
            width=130,
            height=36,
            corner_radius=10,
            fg_color="#5865F2",
            hover_color="#707CF8",
            font=("Segoe UI", 12),
            command=lambda: webbrowser.open(DISCORD_URL),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            footer,
            text="GitHub",
            width=120,
            height=36,
            corner_radius=10,
            fg_color="#2D313A",
            hover_color="#3A404A",
            font=("Segoe UI", 12),
            command=lambda: webbrowser.open(GITHUB_URL),
        ).pack(side="left")

        ctk.CTkLabel(
            footer,
            text="CREATED BY GC",
            font=("Segoe UI", 12, "bold"),
            text_color="#FF4FA3",
        ).pack(side="right")

    def select_path(self) -> None:
        path = filedialog.askdirectory(initialdir=self.save_path)
        if path:
            self.save_path = path
            self.status_label.configure(text=f"Folder: {os.path.basename(path)}", text_color=ACCENT_COLOR)

    def check_bundled_tools(self) -> None:
        if self.ffmpeg_location:
            self.status_label.configure(text="Ready to Fetch")
        else:
            self.status_label.configure(text="FFmpeg not found", text_color="#FF6B6B")
            messagebox.showwarning(
                "FortyFetch",
                "FFmpeg/FFprobe not found in assets or system PATH. Downloads may fail.",
            )

    def check_and_update_ytdlp(self) -> None:
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if proc.returncode == 0:
                output = (proc.stdout or "") + (proc.stderr or "")
                if "Successfully installed" in output:
                    self.after(0, lambda: self.speed_label.configure(text="yt-dlp updated"))
        except Exception:
            self.after(0, lambda: self.speed_label.configure(text="yt-dlp check skipped"))

    def start_manual_update_thread(self) -> None:
        self.status_label.configure(text="Checking for updates...", text_color="#F5F9FF")
        self.speed_label.configure(text="Please wait...")
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

    def check_app_update_silently(self) -> None:
        try:
            tag, download_url = self._fetch_latest_app_release_details()
            if tag and download_url and self._is_version_newer(tag, APP_VERSION):
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, f"FortyFetch_update_{tag}.exe")

                self._download_file(download_url, temp_file_path)

                if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 1024 * 1024:
                    self.pending_update_path = temp_file_path
        except Exception:
            pass

    def prompt_and_install_app_update(self, tag: str, download_url: str) -> None:
        want_update = messagebox.askyesno(
            "FortyFetch Update",
            f"A new version of FortyFetch (v{tag}) is available.\n\n"
            "Would you like to download and install it now?\n"
            "The app will restart automatically after the update.",
        )
        if not want_update:
            self.status_label.configure(text="Checking tool updates...", text_color="#F5F9FF")
            threading.Thread(target=self._check_and_update_tools, daemon=True).start()
            return

        self.status_label.configure(text=f"Downloading FortyFetch v{tag}...", text_color=ACCENT_COLOR)
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.speed_label.configure(text="Connecting...")

        def download_and_apply():
            try:
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

    def _update_download_progress(self, percent: float) -> None:
        self.progress_bar.set(percent / 100)
        self.percent_label.configure(text=f"{int(percent)}%")
        self.speed_label.configure(text="Downloading setup files...")

    def _apply_manual_update_and_restart(self, temp_file_path: str) -> None:
        current_exe = sys.executable
        powershell_cmd = f"Start-Sleep -Seconds 2; Copy-Item -Path '{temp_file_path}' -Destination '{current_exe}' -Force; Start-Process '{current_exe}'; Remove-Item -Path '{temp_file_path}'"
        try:
            subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", powershell_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
            self.destroy()
        except Exception as exc:
            traceback.print_exc()
            messagebox.showerror("FortyFetch Update", f"Failed to restart and apply update: {exc}")

    def on_exit(self) -> None:
        if getattr(self, "pending_update_path", None) and os.path.exists(self.pending_update_path):
            current_exe = sys.executable
            new_exe = self.pending_update_path
            powershell_cmd = f"Start-Sleep -Seconds 2; Copy-Item -Path '{new_exe}' -Destination '{current_exe}' -Force; Remove-Item -Path '{new_exe}'"
            try:
                subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", powershell_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                traceback.print_exc()
        self.destroy()

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
                self.status_label.configure(text="Update successful", text_color=ACCENT_COLOR)
            else:
                self.status_label.configure(text="No updates available", text_color=ACCENT_COLOR)

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
            latest = self._fetch_latest_ytdlp_version()
            if latest and self._is_version_newer(latest, YTDLP_VERSION):
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
        req = urlrequest.Request(url, headers={"User-Agent": "FortyFetch/1.0"})
        with urlrequest.urlopen(req, timeout=90) as resp, open(target_path, "wb") as out:
            shutil.copyfileobj(resp, out)

    def _extract_ffmpeg_bins(self, zip_path: str, extract_dir: str) -> tuple[str, str]:
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

    def show_update_help(self) -> None:
        pop = ctk.CTkToplevel(self)
        pop.title("Update Help")
        pop.geometry("560x420")
        pop.configure(fg_color=BG_COLOR)
        pop.resizable(False, False)
        self._bring_popup_front(pop)

        ctk.CTkLabel(pop, text="Update Instructions", font=("Impact", 38), text_color=ACCENT_COLOR).pack(pady=(16, 10))

        help_text = (
            "1. Click 'Check for Updates' from the top-right.\n"
            "2. FortyFetch checks yt-dlp, ffmpeg, and ffprobe.\n"
            "3. If updates are available, they are installed automatically when possible.\n"
            "4. You will see one of these results:\n"
            "   - Update successful\n"
            "   - No updates available\n\n"
            "Tip: Keep internet ON while checking updates."
        )
        ctk.CTkLabel(
            pop,
            text=help_text,
            justify="left",
            anchor="w",
            font=("Segoe UI", 14),
            text_color="#DCE6F9",
        ).pack(fill="both", expand=True, padx=24, pady=(4, 14))

        ctk.CTkButton(
            pop,
            text="Close",
            width=120,
            height=40,
            corner_radius=10,
            fg_color="#2C3039",
            hover_color="#3A404A",
            font=("Segoe UI", 14),
            command=pop.destroy,
        ).pack(pady=(0, 16))

    def progress_hook(self, data: dict) -> None:
        status = data.get("status")
        if status == "downloading":
            p_str = data.get("_percent_str", "0%").replace("%", "").strip()
            speed = data.get("_speed_str", "Waiting...")
            eta = data.get("_eta_str", "")
            try:
                # Strip ANSI escape codes if present
                clean_p_str = re.sub(r'\x1b\[[0-9;]*m', '', p_str)
                match = re.search(r'\d+\.\d+|\d+', clean_p_str)
                p_val = float(match.group(0)) if match else 0.0
                p_val = max(0.0, min(100.0, p_val))
            except Exception:
                p_val = 0.0

            eta_text = f" | ETA {eta}" if eta else ""

            def _update():
                self.progress_bar.set(p_val / 100)
                self.percent_label.configure(text=f"{int(p_val)}%")
                self.speed_label.configure(text=f"{speed}{eta_text}")
                self.status_label.configure(text="Fetching data...")

            self.after(0, _update)

        elif status == "finished":
            self.after(0, lambda: self.status_label.configure(text="Finalizing with FFmpeg..."))

    def start_download_thread(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("FortyFetch", "Please paste a video link.")
            return

        if not self.save_path:
            messagebox.showwarning("FortyFetch", "Please select a save folder.")
            return

        if not self.ffmpeg_location:
            messagebox.showerror("FortyFetch", "FFmpeg not available. Put ffmpeg.exe and ffprobe.exe in assets.")
            return

        self.download_btn.configure(state="disabled", text="FETCHING...", fg_color="#2E323A")
        self.status_label.configure(text="Preparing download...")
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
        self.speed_label.configure(text="Waiting...")

        choice = self.selected_quality.get()
        threading.Thread(target=self.download_video, args=(url, choice), daemon=True).start()

    def _format_for_quality(self, choice: str) -> tuple[str, bool]:
        if "MP3" in choice:
            return "bestaudio/best", True

        match = re.search(r"(\d+)p", choice)
        height = match.group(1) if match else "1080"

        fmt = (
            f"bestvideo[height<={height}][fps<=60]+bestaudio/"
            f"best[height<={height}][fps<=60]/best"
        )
        return fmt, False

    def download_video(self, url: str, choice: str) -> None:
        fmt, is_mp3 = self._format_for_quality(choice)

        ydl_opts: dict = {
            "progress_hooks": [self.progress_hook],
            "outtmpl": os.path.join(self.save_path, "%(title).180B [%(id)s].%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "ffmpeg_location": self.ffmpeg_location,
            "format": fmt,
            "merge_output_format": "mp4",
            "nocheckcertificate": True,
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
                title = info.get("title", "download") if isinstance(info, dict) else "download"

            def _success():
                self.status_label.configure(text=f"Completed: {title}", text_color=ACCENT_COLOR)
                messagebox.showinfo("FortyFetch", "Download successful.")

            self.after(0, _success)
        except Exception as exc:
            traceback.print_exc()
            error_msg = str(exc)[:220]
            
            def _error():
                self.status_label.configure(text="Download failed", text_color="#FF6B6B")
                messagebox.showerror("FortyFetch", f"Error: {error_msg}")

            self.after(0, _error)
        finally:
            self.after(0, self._reset_after_download)

    def _reset_after_download(self) -> None:
        self.download_btn.configure(state="normal", text="START FETCH", fg_color=ACCENT_COLOR)
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")

    def show_donation_info(self) -> None:
        pop = ctk.CTkToplevel(self)
        pop.title("Buy Me a Coffee")
        pop.geometry("460x620")
        pop.configure(fg_color=BG_COLOR)
        pop.resizable(False, False)
        self._bring_popup_front(pop)

        ctk.CTkLabel(pop, text="Buy me a Coffee", font=("Impact", 42), text_color=ACCENT_COLOR).pack(pady=(16, 12))

        qr_path = os.path.join(self.assets_dir, "qr_code.png")
        if os.path.exists(qr_path):
            try:
                img_data = Image.open(qr_path)
                qr_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(320, 320))
                qr_label = ctk.CTkLabel(pop, image=qr_img, text="")
                qr_label.image = qr_img
                qr_label.pack(pady=8)
            except Exception:
                ctk.CTkLabel(pop, text="Unable to load QR image.", text_color="#FF6B6B", font=("Segoe UI", 16)).pack()
        else:
            ctk.CTkLabel(pop, text="QR code not found in assets.", text_color="#FF6B6B", font=("Segoe UI", 16)).pack()

        ctk.CTkLabel(pop, text=f"UPI: {UPI_ID}", font=("Segoe UI", 18, "bold"), text_color=ACCENT_COLOR).pack(pady=(10, 4))
        
        ctk.CTkButton(
            pop,
            text="PayPal Me",
            width=200,
            height=38,
            corner_radius=10,
            fg_color="#003087",
            hover_color="#0079C1",
            text_color="#FFFFFF",
            font=("Segoe UI", 14, "bold"),
            command=lambda: webbrowser.open(PAYPAL_URL),
        ).pack(pady=(8, 14))

        ctk.CTkButton(
            pop,
            text="Close",
            width=130,
            height=42,
            corner_radius=10,
            fg_color="#2C3039",
            hover_color="#3A404A",
            font=("Segoe UI", 14),
            command=pop.destroy,
        ).pack()

    def _bring_popup_front(self, pop: ctk.CTkToplevel) -> None:
        pop.transient(self)
        pop.lift()
        pop.attributes("-topmost", True)
        pop.after(250, lambda: pop.attributes("-topmost", False))
        pop.focus_force()


if __name__ == "__main__":
    if should_exit_early_for_packaged_relaunch():
        sys.exit(0)
    app = FortyFetchApp()
    app.mainloop()
