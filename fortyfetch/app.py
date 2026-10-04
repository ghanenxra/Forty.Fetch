import customtkinter as ctk
import sys
import os
from fortyfetch.core.common import *
from fortyfetch.core.settings import SettingsMixin
from fortyfetch.ui.theme import ThemeMixin
from fortyfetch.core.downloader import DownloaderMixin
from fortyfetch.ui.layout import LayoutMixin
from fortyfetch.ui.views.home import HomeViewMixin
from fortyfetch.ui.views.downloads import DownloadsViewMixin
from fortyfetch.ui.views.settings import SettingsViewMixin
from fortyfetch.ui.views.about import AboutViewMixin
from fortyfetch.core.updater import UpdaterMixin


class FortyFetchApp(SettingsMixin, ThemeMixin, DownloaderMixin, LayoutMixin, HomeViewMixin, DownloadsViewMixin, SettingsViewMixin, AboutViewMixin, UpdaterMixin, ctk.CTk):
        def __init__(self) -> None:
            super().__init__()

            # History, Navigation & Settings
            self.downloads_history: list[dict] = []
            self.active_nav = "home"
            self._last_progress_time = 0.0
            self._qr_image_cached = None
            self.settings = self._load_settings()

            # Appearance & Base Window Configuration
            saved_theme = self.settings.get("theme", "dark")
            ctk.set_appearance_mode(saved_theme)
            self.title(APP_TITLE)
            self.geometry("1400x900")
            self.minsize(1120, 720)
            self.configure(fg_color=BG_COLOR)

            # Fast paths & state initialization
            self.assets_dir = resource_path("assets")
            self.ffmpeg_exe = os.path.join(self.assets_dir, "ffmpeg.exe")
            self.ffprobe_exe = os.path.join(self.assets_dir, "ffprobe.exe")
            self.ffmpeg_location = self._resolve_ffmpeg_location()

            self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
            default_q = self.settings.get("default_quality", "1080p 60fps")
            if default_q not in QUALITY_OPTIONS:
                default_q = "1080p 60fps"
            self.selected_quality = ctk.StringVar(value=default_q)

            self.pending_update_path = None
            self.protocol("WM_DELETE_WINDOW", self.on_exit)

            # Window icon (fast local check)
            self._set_icon()

            # Build Primary UI Layout (Home View built first, others lazy-loaded)
            self._build_layout()

            # Verify local tools after UI is displayed (zero network, instantaneous)
            self.after(200, self.check_bundled_tools)
