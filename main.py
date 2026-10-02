import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from tkinter import Canvas, filedialog, messagebox

import customtkinter as ctk

# Enable High-DPI Awareness for Windows before any window creation
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ==========================================
# PALETTE & DESIGN TOKENS (LIGHT, DARK)
# ==========================================
BG_COLOR = ("#F1F5F9", "#05080D")
PANEL_COLOR = ("#FFFFFF", "#0B1420")
PANEL_ELEVATED = ("#F8FAFC", "#101B28")
PANEL_HOVER = ("#E2E8F0", "#182638")
BORDER_COLOR = ("#E2E8F0", "#162334")
BORDER_LIGHT = ("#CBD5E1", "#22354D")

ACCENT_CYAN = ("#008FA8", "#00D9FF")
ACCENT_CYAN_HOVER = ("#00788E", "#00B5D6")
ACCENT_CYAN_SUBTLE = ("#E0F7FA", "#0D2536")
ACCENT_BLUE = ("#0284C7", "#168CFF")
ACCENT_GREEN = ("#059669", "#10B981")
ACCENT_GREEN_HOVER = ("#047857", "#059669")
ACCENT_GREEN_SUBTLE = ("#DCFCE7", "#092019")
ACCENT_ORANGE = ("#EA580C", "#FF813F")
ACCENT_ORANGE_HOVER = ("#C2410C", "#FF985C")
ACCENT_DISCORD = ("#5865F2", "#5865F2")
ACCENT_DISCORD_HOVER = ("#4752C4", "#707CF8")
ACCENT_PINK = ("#DB2777", "#FF4FA3")

TEXT_PRIMARY = ("#0F172A", "#FFFFFF")
TEXT_MUTED = ("#64748B", "#8D96A7")
BUTTON_TEXT = ("#FFFFFF", "#05080D")
INPUT_BG = ("#F8FAFC", "#060B12")
BADGE_BG = ("#EEF2F6", "#060C14")
PROGRESS_TRACK = ("#E2E8F0", "#060B12")
PLACEHOLDER_COLOR = ("#94A3B8", "#4D5869")

APP_VERSION = "3.0.2"
APP_TITLE = f"FortyFetch v{APP_VERSION} - High Speed YouTube Downloader"
DISCORD_URL = "https://discord.com/users/1323161662739714120"
GITHUB_URL = "https://github.com/ghanenxra"
PAYPAL_URL = "https://www.paypal.com/paypalme/ghanenxra"
UPI_ID = "9024810096@fam"

QUALITY_OPTIONS = [
    "4320p 60fps (8K)",
    "2160p 60fps (4K)",
    "1440p 60fps",
    "1080p 60fps",
    "1080p",
    "720p 60fps",
    "480p",
    "Audio Only (MP3)",
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


# ==========================================
# OPTIMIZED CUSTOM WIDGETS
# ==========================================
class CircularProgress(Canvas):
    """Futuristic circular progress gauge with glowing cyan arc and centered percentage."""
    def __init__(self, master, size=60, current_mode="dark", **kwargs):
        self._current_mode = current_mode.lower()
        bg_col = "#FFFFFF" if self._current_mode == "light" else "#0B1420"
        super().__init__(
            master,
            width=size,
            height=size,
            bg=bg_col,
            highlightthickness=0,
            **kwargs
        )
        self.size = size
        self.percentage = 0.0

        margin = 5
        x0, y0 = margin, margin
        x1, y1 = size - margin, size - margin
        ring_col = "#E2E8F0" if self._current_mode == "light" else "#101B28"
        cyan_col = "#008FA8" if self._current_mode == "light" else "#00D9FF"
        text_col = "#64748B" if self._current_mode == "light" else "#8D96A7"

        self.ring_id = self.create_oval(x0, y0, x1, y1, outline=ring_col, width=5)
        self.arc_id = self.create_arc(
            x0, y0, x1, y1,
            start=90,
            extent=0,
            outline=cyan_col,
            width=5,
            style="arc"
        )
        self.text_id = self.create_text(
            size // 2,
            size // 2,
            text="0%",
            fill=text_col,
            font=("Segoe UI", 11, "bold")
        )

    def set_theme(self, mode: str) -> None:
        self._current_mode = mode.lower()
        is_light = (self._current_mode == "light")
        bg_col = "#FFFFFF" if is_light else "#0B1420"
        ring_col = "#E2E8F0" if is_light else "#101B28"
        cyan_col = "#008FA8" if is_light else "#00D9FF"
        muted_col = "#64748B" if is_light else "#8D96A7"

        self.configure(bg=bg_col)
        self.itemconfig(self.ring_id, outline=ring_col)
        self.itemconfig(
            self.arc_id,
            outline=cyan_col if self.percentage > 0 else ring_col
        )
        self.itemconfig(
            self.text_id,
            fill=cyan_col if self.percentage > 0 else muted_col
        )

    def set_progress(self, percent: float) -> None:
        self.percentage = max(0.0, min(100.0, percent))
        extent = -(self.percentage / 100.0) * 359.99
        is_light = (self._current_mode == "light")
        cyan_col = "#008FA8" if is_light else "#00D9FF"
        ring_col = "#E2E8F0" if is_light else "#101B28"
        muted_col = "#64748B" if is_light else "#8D96A7"

        self.itemconfig(
            self.arc_id,
            extent=extent,
            outline=cyan_col if self.percentage > 0 else ring_col
        )
        self.itemconfig(
            self.text_id,
            text=f"{int(self.percentage)}%",
            fill=cyan_col if self.percentage > 0 else muted_col
        )


class MountainIllustration(Canvas):
    """Subtle futuristic dark night/mountain wireframe illustration for sidebar footer."""
    def __init__(self, master, width=266, height=90, current_mode="dark", **kwargs):
        self._current_mode = current_mode.lower()
        bg_col = "#FFFFFF" if current_mode == "light" else "#0B1420"
        super().__init__(
            master,
            width=width,
            height=height,
            bg=bg_col,
            highlightthickness=0,
            **kwargs
        )
        self.width = width
        self.height = height
        self._render_static_scene(self._current_mode)

    def set_theme(self, mode: str) -> None:
        self._current_mode = mode.lower()
        bg_col = "#FFFFFF" if self._current_mode == "light" else "#0B1420"
        self.configure(bg=bg_col)
        self.delete("all")
        self._render_static_scene(self._current_mode)

    def _render_static_scene(self, mode: str) -> None:
        w = self.width
        h = self.height

        if mode == "light":
            # Soft atmospheric light mountain silhouettes
            back_points = [
                0, h, 0, h - 30, 35, h - 50, 75, h - 36, 120, h - 60,
                165, h - 40, 205, h - 68, w, h - 32, w, h
            ]
            self.create_polygon(back_points, fill="#E2E8F0", outline="")

            mid_points = [
                0, h, 0, h - 18, 50, h - 38, 95, h - 24, 150, h - 48,
                190, h - 30, w, h - 44, w, h
            ]
            self.create_polygon(mid_points, fill="#CBD5E1", outline="")

            ridge_lines = [
                (0, h - 18, 50, h - 38),
                (50, h - 38, 95, h - 24),
                (95, h - 24, 150, h - 48),
                (150, h - 48, 190, h - 30),
                (190, h - 30, w, h - 44)
            ]
            for x1, y1, x2, y2 in ridge_lines:
                self.create_line(x1, y1, x2, y2, fill="#94A3B8", width=1.2)

            front_points = [
                0, h, 20, h - 24, 65, h - 14, 110, h - 30,
                160, h - 16, 215, h - 34, w, h - 18, w, h
            ]
            self.create_polygon(front_points, fill="#BAC7D5", outline="")
            crest_lines = [
                (0, h, 20, h - 24), (20, h - 24, 65, h - 14), (65, h - 14, 110, h - 30),
                (110, h - 30, 160, h - 16), (160, h - 16, 215, h - 34), (215, h - 34, w, h - 18)
            ]
            for x1, y1, x2, y2 in crest_lines:
                self.create_line(x1, y1, x2, y2, fill="#008FA8", width=1.2)
        else:
            # Soft stars
            stars = [
                (25, 14), (65, 24), (115, 10), (170, 16), (210, 12),
                (45, 34), (140, 28), (195, 32)
            ]
            for sx, sy in stars:
                self.create_oval(sx, sy, sx + 1.5, sy + 1.5, fill="#1B3852", outline="")

            # Back mountain layer (dark navy silhouette)
            back_points = [
                0, h, 0, h - 30, 35, h - 50, 75, h - 36, 120, h - 60,
                165, h - 40, 205, h - 68, w, h - 32, w, h
            ]
            self.create_polygon(back_points, fill="#07101B", outline="")

            # Mid mountain layer
            mid_points = [
                0, h, 0, h - 18, 50, h - 38, 95, h - 24, 150, h - 48,
                190, h - 30, w, h - 44, w, h
            ]
            self.create_polygon(mid_points, fill="#0A1624", outline="")

            # Glowing cyan ridge lines
            ridge_lines = [
                (0, h - 18, 50, h - 38),
                (50, h - 38, 95, h - 24),
                (95, h - 24, 150, h - 48),
                (150, h - 48, 190, h - 30),
                (190, h - 30, w, h - 44)
            ]
            for x1, y1, x2, y2 in ridge_lines:
                self.create_line(x1, y1, x2, y2, fill="#0F334A", width=1.2)

            # Front mountain layer with glowing ridge crests
            front_points = [
                0, h, 20, h - 24, 65, h - 14, 110, h - 30,
                160, h - 16, 215, h - 34, w, h - 18, w, h
            ]
            self.create_polygon(front_points, fill="#0D1E30", outline="")
            crest_lines = [
                (0, h, 20, h - 24), (20, h - 24, 65, h - 14), (65, h - 14, 110, h - 30),
                (110, h - 30, 160, h - 16), (160, h - 16, 215, h - 34), (215, h - 34, w, h - 18)
            ]
            for x1, y1, x2, y2 in crest_lines:
                self.create_line(x1, y1, x2, y2, fill="#00D9FF", width=1.2)


# ==========================================
# MAIN APPLICATION
# ==========================================
class FortyFetchApp(ctk.CTk):
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

    def _load_settings(self) -> dict:
        config_path = os.path.join(os.path.expanduser("~"), ".fortyfetch_settings.json")
        default_settings = {
            "theme": "dark",
            "default_quality": "1080p 60fps",
            "download_subtitles": False,
            "embed_thumbnail": True,
            "embed_metadata": True,
            "max_connections": "5",
            "buffer_size": "64 KB",
            "network_opt": True,
            "start_with_windows": False,
            "minimize_to_tray": False,
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_settings.update(data)
            except Exception:
                pass
        return default_settings

    def _save_settings(self) -> None:
        config_path = os.path.join(os.path.expanduser("~"), ".fortyfetch_settings.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass

    def set_theme(self, mode: str) -> None:
        norm_mode = mode.lower()
        if norm_mode not in ("dark", "light", "system"):
            norm_mode = "dark"
        ctk.set_appearance_mode(norm_mode)
        self.settings["theme"] = norm_mode
        self._save_settings()

        effective_mode = norm_mode
        if effective_mode == "system":
            effective_mode = ctk.get_appearance_mode().lower()

        if hasattr(self, "circular_progress"):
            self.circular_progress.set_theme(effective_mode)
        if hasattr(self, "mountain_canvas"):
            self.mountain_canvas.set_theme(effective_mode)
        if hasattr(self, "theme_switch_var"):
            self.theme_switch_var.set(effective_mode == "dark")
        if hasattr(self, "theme_menu_var"):
            self.theme_menu_var.set(norm_mode.capitalize())

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

    # ==========================================
    # SHELL & LAYOUT CREATION
    # ==========================================
    def _build_layout(self) -> None:
        # Root container
        self.root_container = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        self.root_container.pack(fill="both", expand=True)

        # Sidebar (270px wide fixed)
        self._build_sidebar()

        # Content Area (Right)
        self.content_area = ctk.CTkFrame(self.root_container, fg_color="transparent", corner_radius=0)
        self.content_area.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=14)

        # Top Header Bar in Content Area
        self._build_header_bar()

        # Page Views Container
        self.views_container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.views_container.pack(fill="both", expand=True)

        # Views Dictionary (Initialized lazily on demand)
        self.views: dict[str, ctk.CTkFrame] = {}

        # Initialize ONLY Home View on startup for maximum speed
        self._init_home_view()
        self.switch_nav("home")

    # ==========================================
    # LEFT SIDEBAR
    # ==========================================
    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(
            self.root_container,
            width=270,
            fg_color=PANEL_COLOR,
            corner_radius=0,
            border_width=1,
            border_color=BORDER_COLOR
        )
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        # Top Brand Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=24, pady=(24, 16))

        logo_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        logo_row.pack(anchor="w")

        ctk.CTkLabel(
            logo_row,
            text="FORTY.",
            font=("Segoe UI", 24, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            logo_row,
            text="FETCH",
            font=("Segoe UI", 24, "bold"),
            text_color=ACCENT_CYAN
        ).pack(side="left")

        ctk.CTkLabel(
            brand_frame,
            text="HIGH SPEED DOWNLOADER",
            font=("Segoe UI", 9, "bold"),
            text_color=TEXT_MUTED
        ).pack(anchor="w", pady=(2, 0))

        # Divider line
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER_COLOR).pack(fill="x", padx=20, pady=(4, 14))

        # Nav Buttons Section
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("home", "▶   Home"),
            ("downloads", "⬇   Downloads"),
            ("settings", "⚙   Settings"),
            ("about", "ⓘ   About"),
        ]

        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=16, pady=0)

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=label,
                anchor="w",
                height=44,
                corner_radius=12,
                fg_color="transparent",
                hover_color=PANEL_HOVER,
                text_color=TEXT_MUTED,
                font=("Segoe UI", 13, "bold"),
                command=lambda k=key: self.switch_nav(k)
            )
            btn.pack(fill="x", pady=3)
            self.nav_buttons[key] = btn

        # Spacer to push footer down
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Mountain wireframe illustration (clean static render)
        saved_theme = self.settings.get("theme", "dark")
        self.mountain_canvas = MountainIllustration(self.sidebar, width=266, height=90, current_mode=saved_theme)
        self.mountain_canvas.pack(fill="x", pady=(0, 8))

        # Footer Version Badge & Credits
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_frame.pack(fill="x", padx=24, pady=(0, 20))

        badge = ctk.CTkFrame(
            footer_frame,
            fg_color=BADGE_BG,
            corner_radius=8,
            border_width=1,
            border_color=BORDER_COLOR
        )
        badge.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            badge,
            text=f"  v{APP_VERSION}  ",
            font=("Consolas", 11, "bold"),
            text_color=ACCENT_CYAN
        ).pack(padx=6, pady=2)

        credit_col = ctk.CTkFrame(footer_frame, fg_color="transparent")
        credit_col.pack(anchor="w")

        ctk.CTkLabel(
            credit_col,
            text="Powered by",
            font=("Segoe UI", 10),
            text_color=TEXT_MUTED
        ).pack(anchor="w")

        ctk.CTkLabel(
            credit_col,
            text="Forty Quinn",
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w")

    def switch_nav(self, key: str) -> None:
        self.active_nav = key

        # Lazy initialize views when clicked for the first time
        if key not in self.views:
            if key == "downloads":
                self._init_downloads_view()
            elif key == "settings":
                self._init_settings_view()
            elif key == "about":
                self._init_about_view()

        # Update button visual states
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color=ACCENT_CYAN_SUBTLE,
                    text_color=ACCENT_CYAN,
                    border_width=1,
                    border_color=ACCENT_CYAN
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_MUTED,
                    border_width=0
                )

        # Show target view
        for k, view in self.views.items():
            if k == key:
                view.pack(fill="both", expand=True)
            else:
                view.pack_forget()

        # Update breadcrumb
        titles = {
            "home": "DASHBOARD // DOWNLOADER",
            "downloads": "TASK MANAGER // DOWNLOADS",
            "settings": "PREFERENCES // SETTINGS",
            "about": "SYSTEM // ABOUT"
        }
        self.breadcrumb_label.configure(text=titles.get(key, "FORTYFETCH"))

    # ==========================================
    # HEADER BAR (TOP RIGHT ACTIONS)
    # ==========================================
    def _build_header_bar(self) -> None:
        top_bar = ctk.CTkFrame(self.content_area, fg_color="transparent", height=38)
        top_bar.pack(fill="x", pady=(0, 10))

        # Breadcrumb / Section tag
        self.breadcrumb_label = ctk.CTkLabel(
            top_bar,
            text="DASHBOARD // DOWNLOADER",
            font=("Consolas", 11, "bold"),
            text_color=TEXT_MUTED
        )
        self.breadcrumb_label.pack(side="left", padx=(6, 0))

        # Action Buttons (Help & Update)
        update_btn = ctk.CTkButton(
            top_bar,
            text="↻  Check for Updates",
            width=165,
            height=34,
            corner_radius=10,
            fg_color=ACCENT_GREEN_SUBTLE,
            hover_color=ACCENT_GREEN_HOVER,
            text_color=ACCENT_GREEN,
            border_width=1,
            border_color=ACCENT_GREEN,
            font=("Segoe UI", 12, "bold"),
            command=self.start_manual_update_thread
        )
        update_btn.pack(side="right")

        help_btn = ctk.CTkButton(
            top_bar,
            text="?  Help",
            width=84,
            height=34,
            corner_radius=10,
            fg_color=PANEL_COLOR,
            hover_color=PANEL_HOVER,
            text_color=TEXT_PRIMARY,
            border_width=1,
            border_color=BORDER_COLOR,
            font=("Segoe UI", 12, "bold"),
            command=self.show_update_help
        )
        help_btn.pack(side="right", padx=(0, 10))

    # ==========================================
    # VIEW 1: HOME (MAIN DOWNLOADER - NO SCROLL)
    # ==========================================
    def _init_home_view(self) -> None:
        # Standard CTkFrame - fits completely on screen without scroll or resize lag
        view = ctk.CTkFrame(self.views_container, fg_color="transparent")
        self.views["home"] = view

        # 1. Branding Center
        brand_container = ctk.CTkFrame(view, fg_color="transparent")
        brand_container.pack(fill="x", pady=(0, 10))

        logo_box = ctk.CTkFrame(brand_container, fg_color="transparent")
        logo_box.pack(anchor="center")

        ctk.CTkLabel(
            logo_box,
            text="FORTY.",
            font=("Segoe UI", 26, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            logo_box,
            text="FETCH",
            font=("Segoe UI", 26, "bold"),
            text_color=ACCENT_CYAN
        ).pack(side="left")

        ctk.CTkLabel(
            brand_container,
            text="H I G H   S P E E D   Y O U T U B E   D O W N L O A D E R",
            font=("Segoe UI", 9, "bold"),
            text_color=TEXT_MUTED
        ).pack(pady=(2, 0))

        # 2. Feature Highlights (3 compact cards)
        features_row = ctk.CTkFrame(view, fg_color="transparent")
        features_row.pack(fill="x", pady=(0, 10))
        features_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="feat")

        features_data = [
            ("⚡", "Blazing Fast", "High speed downloads"),
            ("🛡", "Safe & Reliable", "No ads, No tracking"),
            ("🎬", "Multiple Formats", "Video, Audio, Playlists"),
        ]

        for i, (icon, title, desc) in enumerate(features_data):
            f_card = ctk.CTkFrame(
                features_row,
                fg_color=PANEL_COLOR,
                corner_radius=12,
                border_width=1,
                border_color=BORDER_COLOR
            )
            f_card.grid(row=0, column=i, padx=6, sticky="ew")

            content = ctk.CTkFrame(f_card, fg_color="transparent")
            content.pack(padx=14, pady=8, fill="x")

            ctk.CTkLabel(
                content,
                text=icon,
                font=("Segoe UI", 18),
                text_color=ACCENT_CYAN
            ).pack(side="left", padx=(0, 10))

            t_box = ctk.CTkFrame(content, fg_color="transparent")
            t_box.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                t_box,
                text=title,
                font=("Segoe UI", 12, "bold"),
                text_color=TEXT_PRIMARY
            ).pack(anchor="w")

            ctk.CTkLabel(
                t_box,
                text=desc,
                font=("Segoe UI", 10),
                text_color=TEXT_MUTED
            ).pack(anchor="w")

        # 3. Main Download Card
        self.download_card = ctk.CTkFrame(
            view,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR
        )
        self.download_card.pack(fill="x", pady=(0, 10))

        card_inner = ctk.CTkFrame(self.download_card, fg_color="transparent")
        card_inner.pack(fill="both", expand=True, padx=20, pady=14)

        # Top row of card
        top_header = ctk.CTkFrame(card_inner, fg_color="transparent")
        top_header.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            top_header,
            text="🔗  PASTE YOUTUBE LINK",
            font=("Segoe UI", 12, "bold"),
            text_color=ACCENT_CYAN
        ).pack(side="left")

        ctk.CTkLabel(
            top_header,
            text="Supports: Video, Playlist, Channel, Shorts ℹ",
            font=("Segoe UI", 10),
            text_color=TEXT_MUTED
        ).pack(side="right")

        # URL Input field with real-time validation
        self.url_container = ctk.CTkFrame(
            card_inner,
            fg_color=INPUT_BG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_COLOR,
            height=46
        )
        self.url_container.pack(fill="x", pady=(0, 10))
        self.url_container.pack_propagate(False)

        ctk.CTkLabel(
            self.url_container,
            text="  ▶  ",
            font=("Segoe UI", 13),
            text_color=ACCENT_CYAN
        ).pack(side="left", padx=(8, 0))

        self.url_entry = ctk.CTkEntry(
            self.url_container,
            fg_color="transparent",
            border_width=0,
            text_color=TEXT_PRIMARY,
            placeholder_text="https://www.youtube.com/watch?v=... or Shorts link",
            placeholder_text_color=PLACEHOLDER_COLOR,
            font=("Segoe UI", 13)
        )
        self.url_entry.pack(side="left", fill="both", expand=True, padx=(4, 10))
        self.url_entry.bind("<KeyRelease>", self._on_url_input_change)

        self.url_validation_badge = ctk.CTkLabel(
            self.url_container,
            text="",
            font=("Segoe UI", 11, "bold"),
            text_color=ACCENT_GREEN
        )
        self.url_validation_badge.pack(side="right", padx=(0, 12))

        # Options Row: Quality & Save Folder
        options_row = ctk.CTkFrame(card_inner, fg_color="transparent")
        options_row.pack(fill="x", pady=(0, 12))
        options_row.grid_columnconfigure((0, 1), weight=1, uniform="opt")

        # Left Column - Quality
        q_box = ctk.CTkFrame(options_row, fg_color="transparent")
        q_box.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkLabel(
            q_box,
            text="🖥  Quality",
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 4))

        self.quality_menu = ctk.CTkOptionMenu(
            q_box,
            variable=self.selected_quality,
            values=QUALITY_OPTIONS,
            height=38,
            corner_radius=10,
            fg_color=PANEL_ELEVATED,
            button_color=ACCENT_CYAN_SUBTLE,
            button_hover_color=PANEL_HOVER,
            text_color=TEXT_PRIMARY,
            dropdown_fg_color=PANEL_COLOR,
            dropdown_hover_color=ACCENT_CYAN_SUBTLE,
            dropdown_text_color=TEXT_PRIMARY,
            font=("Segoe UI", 12, "bold")
        )
        self.quality_menu.pack(fill="x")

        # Right Column - Save Folder
        folder_box = ctk.CTkFrame(options_row, fg_color="transparent")
        folder_box.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        ctk.CTkLabel(
            folder_box,
            text="📁  Save Folder",
            font=("Segoe UI", 11, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 4))

        folder_input_row = ctk.CTkFrame(folder_box, fg_color="transparent")
        folder_input_row.pack(fill="x")

        self.folder_display = ctk.CTkEntry(
            folder_input_row,
            height=38,
            corner_radius=10,
            fg_color=PANEL_ELEVATED,
            border_width=1,
            border_color=BORDER_COLOR,
            text_color=TEXT_MUTED,
            font=("Segoe UI", 11)
        )
        self.folder_display.insert(0, self.save_path)
        self.folder_display.configure(state="disabled")
        self.folder_display.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(
            folder_input_row,
            text="Browse...",
            width=90,
            height=38,
            corner_radius=10,
            fg_color=PANEL_ELEVATED,
            hover_color=PANEL_HOVER,
            text_color=TEXT_PRIMARY,
            border_width=1,
            border_color=BORDER_COLOR,
            font=("Segoe UI", 12, "bold"),
            command=self.select_path
        )
        browse_btn.pack(side="right")

        # Start Fetch Button (Centered, Large, Glowing Cyan)
        btn_wrapper = ctk.CTkFrame(card_inner, fg_color="transparent")
        btn_wrapper.pack(fill="x", pady=(2, 0))

        self.download_btn = ctk.CTkButton(
            btn_wrapper,
            text="⬇   START FETCH",
            width=320,
            height=44,
            corner_radius=14,
            fg_color=ACCENT_CYAN,
            hover_color=ACCENT_CYAN_HOVER,
            text_color=BUTTON_TEXT,
            font=("Segoe UI", 14, "bold"),
            command=self.start_download_thread
        )
        self.download_btn.pack(anchor="center")

        # 4. Progress Card
        self.progress_card = ctk.CTkFrame(
            view,
            fg_color=PANEL_COLOR,
            corner_radius=16,
            border_width=1,
            border_color=BORDER_COLOR
        )
        self.progress_card.pack(fill="x", pady=(0, 10))

        p_inner = ctk.CTkFrame(self.progress_card, fg_color="transparent")
        p_inner.pack(fill="both", expand=True, padx=18, pady=10)

        # Left: Circular gauge
        saved_theme = self.settings.get("theme", "dark")
        self.circular_progress = CircularProgress(p_inner, size=60, current_mode=saved_theme)
        self.circular_progress.pack(side="left", padx=(0, 16))

        # Middle: Dynamic Status & Progress Bar
        mid_p = ctk.CTkFrame(p_inner, fg_color="transparent")
        mid_p.pack(side="left", fill="both", expand=True)

        status_header = ctk.CTkFrame(mid_p, fg_color="transparent")
        status_header.pack(fill="x", pady=(1, 4))

        self.status_label = ctk.CTkLabel(
            status_header,
            text="Ready to Fetch",
            font=("Segoe UI", 14, "bold"),
            text_color=TEXT_PRIMARY
        )
        self.status_label.pack(side="left")

        self.percent_label = ctk.CTkLabel(
            status_header,
            text="0%",
            font=("Consolas", 13, "bold"),
            text_color=ACCENT_CYAN
        )
        self.percent_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            mid_p,
            height=8,
            corner_radius=5,
            fg_color=PROGRESS_TRACK,
            progress_color=ACCENT_CYAN
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 4))

        details_row = ctk.CTkFrame(mid_p, fg_color="transparent")
        details_row.pack(fill="x")

        self.speed_label = ctk.CTkLabel(
            details_row,
            text="Idle • Ready for input",
            font=("Segoe UI", 10),
            text_color=TEXT_MUTED
        )
        self.speed_label.pack(side="left")

        # Right: Bundled build mode tag
        right_p = ctk.CTkFrame(p_inner, fg_color="transparent")
        right_p.pack(side="right", padx=(14, 0))

        ctk.CTkLabel(
            right_p,
            text="Bundled build mode",
            font=("Segoe UI", 10, "italic"),
            text_color=TEXT_MUTED
        ).pack(anchor="e")

        # 5. Bottom Actions Row
        footer_row = ctk.CTkFrame(view, fg_color="transparent")
        footer_row.pack(fill="x", pady=(2, 0))

        ctk.CTkButton(
            footer_row,
            text="☕  Buy Me a Coffee",
            width=150,
            height=32,
            corner_radius=9,
            fg_color=ACCENT_ORANGE,
            hover_color=ACCENT_ORANGE_HOVER,
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=self.show_donation_info
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            footer_row,
            text="Discord",
            width=100,
            height=32,
            corner_radius=9,
            fg_color=ACCENT_DISCORD,
            hover_color=ACCENT_DISCORD_HOVER,
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=lambda: webbrowser.open(DISCORD_URL)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            footer_row,
            text="GitHub",
            width=95,
            height=32,
            corner_radius=9,
            fg_color=PANEL_ELEVATED,
            hover_color=PANEL_HOVER,
            text_color=TEXT_PRIMARY,
            border_width=1,
            border_color=BORDER_COLOR,
            font=("Segoe UI", 11, "bold"),
            command=lambda: webbrowser.open(GITHUB_URL)
        ).pack(side="left")

        ctk.CTkLabel(
            footer_row,
            text="CREATED BY GC",
            font=("Segoe UI", 11, "bold"),
            text_color=ACCENT_PINK
        ).pack(side="right", padx=(0, 4))

    def _on_url_input_change(self, event=None) -> None:
        url = self.url_entry.get().strip()
        is_youtube = bool(re.search(r"(youtube\.com|youtu\.be)", url, re.IGNORECASE))
        if is_youtube:
            self.url_container.configure(border_color=ACCENT_CYAN, border_width=2)
            self.url_validation_badge.configure(text="✓ Link Detected", text_color=ACCENT_GREEN)
        elif url:
            self.url_container.configure(border_color=BORDER_LIGHT, border_width=1)
            self.url_validation_badge.configure(text="", text_color=TEXT_MUTED)
        else:
            self.url_container.configure(border_color=BORDER_COLOR, border_width=1)
            self.url_validation_badge.configure(text="", text_color=TEXT_MUTED)

    # ==========================================
    # VIEW 2: DOWNLOADS (NO SCROLL)
    # ==========================================
    def _init_downloads_view(self) -> None:
        if "downloads" in self.views:
            return

        view = ctk.CTkFrame(self.views_container, fg_color="transparent")
        self.views["downloads"] = view

        # Top Control Bar
        top_ctrl = ctk.CTkFrame(view, fg_color=PANEL_COLOR, corner_radius=16, border_width=1, border_color=BORDER_COLOR)
        top_ctrl.pack(fill="x", pady=(0, 12))

        ctrl_inner = ctk.CTkFrame(top_ctrl, fg_color="transparent")
        ctrl_inner.pack(fill="x", padx=20, pady=12)

        ctk.CTkLabel(
            ctrl_inner,
            text="Downloads Queue & History",
            font=("Segoe UI", 16, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkButton(
            ctrl_inner,
            text="📂  Open Downloads Folder",
            width=180,
            height=34,
            corner_radius=10,
            fg_color=PANEL_ELEVATED,
            hover_color=PANEL_HOVER,
            border_width=1,
            border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY,
            font=("Segoe UI", 12, "bold"),
            command=lambda: os.startfile(self.save_path) if os.path.exists(self.save_path) else None
        ).pack(side="right")

        ctk.CTkButton(
            ctrl_inner,
            text="Clear Finished",
            width=115,
            height=34,
            corner_radius=10,
            fg_color=PANEL_ELEVATED,
            hover_color=PANEL_HOVER,
            text_color=TEXT_MUTED,
            font=("Segoe UI", 12),
            command=self._clear_completed_downloads
        ).pack(side="right", padx=(0, 10))

        # Downloads Cards Container (Regular CTkFrame - No scrollbar)
        self.downloads_container = ctk.CTkFrame(view, fg_color="transparent")
        self.downloads_container.pack(fill="both", expand=True)

        self.empty_downloads_label = ctk.CTkLabel(
            self.downloads_container,
            text="No active or past downloads in this session.\nPaste a link on the Home page to start fetching.",
            font=("Segoe UI", 14),
            text_color=TEXT_MUTED
        )

        if not self.downloads_history:
            self.empty_downloads_label.pack(pady=80)
        else:
            for item in self.downloads_history:
                self._render_download_card(item)

    def _render_download_card(self, item: dict) -> None:
        if not hasattr(self, "downloads_container"):
            return

        if hasattr(self, "empty_downloads_label") and self.empty_downloads_label.winfo_ismapped():
            self.empty_downloads_label.pack_forget()

        card = ctk.CTkFrame(
            self.downloads_container,
            fg_color=PANEL_COLOR,
            corner_radius=14,
            border_width=1,
            border_color=BORDER_COLOR
        )
        card.pack(fill="x", pady=5)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=12)

        # Left Icon Badge
        icon_frame = ctk.CTkFrame(inner, width=42, height=42, corner_radius=10, fg_color=PANEL_ELEVATED)
        icon_frame.pack(side="left", padx=(0, 14))
        icon_frame.pack_propagate(False)

        ctk.CTkLabel(
            icon_frame,
            text="🎵" if "MP3" in item.get("format", "") else "🎬",
            font=("Segoe UI", 16)
        ).pack(expand=True)

        # Center info
        info_col = ctk.CTkFrame(inner, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            info_col,
            text=item.get("title", "YouTube Video"),
            font=("Segoe UI", 13, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w")

        meta_text = f"{item.get('format', '1080p')} • {item.get('status', 'Completed')}"
        ctk.CTkLabel(
            info_col,
            text=meta_text,
            font=("Segoe UI", 10),
            text_color=TEXT_MUTED
        ).pack(anchor="w", pady=(2, 4))

        # Progress bar
        pbar = ctk.CTkProgressBar(
            info_col,
            height=6,
            corner_radius=4,
            fg_color=PROGRESS_TRACK,
            progress_color=ACCENT_GREEN if item.get("status") == "Completed ✓" else ACCENT_CYAN
        )
        pbar.set(item.get("progress", 1.0))
        pbar.pack(fill="x")

        # Right Action Buttons
        right_col = ctk.CTkFrame(inner, fg_color="transparent")
        right_col.pack(side="right", padx=(14, 0))

        is_completed = item.get("status") == "Completed ✓"
        status_badge = ctk.CTkFrame(
            right_col,
            fg_color=ACCENT_GREEN_SUBTLE if is_completed else PANEL_ELEVATED,
            corner_radius=8,
            border_width=1,
            border_color=ACCENT_GREEN if is_completed else ACCENT_ORANGE
        )
        status_badge.pack(anchor="e", pady=(0, 6))

        ctk.CTkLabel(
            status_badge,
            text=f"  {item.get('status', 'Done')}  ",
            font=("Segoe UI", 10, "bold"),
            text_color=ACCENT_GREEN if is_completed else ACCENT_ORANGE
        ).pack(padx=6, pady=2)

        if os.path.exists(self.save_path):
            ctk.CTkButton(
                right_col,
                text="Open Folder",
                width=95,
                height=28,
                corner_radius=8,
                fg_color=PANEL_ELEVATED,
                hover_color=PANEL_HOVER,
                text_color=TEXT_PRIMARY,
                font=("Segoe UI", 11),
                command=lambda: os.startfile(self.save_path)
            ).pack(anchor="e")

    def _clear_completed_downloads(self) -> None:
        self.downloads_history.clear()
        if hasattr(self, "downloads_container"):
            for widget in self.downloads_container.winfo_children():
                widget.destroy()
            self.empty_downloads_label = ctk.CTkLabel(
                self.downloads_container,
                text="No active or past downloads in this session.\nPaste a link on the Home page to start fetching.",
                font=("Segoe UI", 14),
                text_color=TEXT_MUTED
            )
            self.empty_downloads_label.pack(pady=80)

    # ==========================================
    # VIEW 3: SETTINGS (SCROLLABLE ONLY HERE)
    # ==========================================
    def _init_settings_view(self) -> None:
        if "settings" in self.views:
            return

        # CTkScrollableFrame is only used in Settings where it is a necessity
        view = ctk.CTkScrollableFrame(self.views_container, fg_color="transparent")
        self.views["settings"] = view

        # Header Title
        ctk.CTkLabel(
            view,
            text="Application Preferences",
            font=("Segoe UI", 22, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(anchor="w", pady=(4, 14))

        categories = [
            ("Appearance", [
                ("Dark Theme", "theme_switch", "theme_toggle"),
                ("Appearance Mode", "theme", "menu", ["Dark", "Light", "System"]),
            ]),
            ("Download Settings", [
                ("Default download quality", "default_quality", "menu", QUALITY_OPTIONS),
                ("Download subtitles automatically when available", "download_subtitles", "switch"),
                ("Embed video thumbnail into audio/video container", "embed_thumbnail", "switch"),
                ("Embed video tags, description & chapters metadata", "embed_metadata", "switch"),
            ]),
            ("Performance & Network", [
                ("Maximum concurrent fragments (speed boost)", "max_connections", "menu", ["2", "5", "8", "10", "16"]),
                ("Network stream buffer size", "buffer_size", "menu", ["16 KB", "64 KB", "128 KB", "256 KB"]),
                ("Enable socket connection optimization", "network_opt", "switch"),
            ]),
            ("General", [
                ("Start with Windows", "start_with_windows", "switch"),
                ("Minimize to system tray on close", "minimize_to_tray", "switch"),
            ])
        ]

        for cat_title, items in categories:
            cat_card = ctk.CTkFrame(
                view,
                fg_color=PANEL_COLOR,
                corner_radius=16,
                border_width=1,
                border_color=BORDER_COLOR
            )
            cat_card.pack(fill="x", pady=6)

            c_inner = ctk.CTkFrame(cat_card, fg_color="transparent")
            c_inner.pack(fill="x", padx=22, pady=16)

            ctk.CTkLabel(
                c_inner,
                text=cat_title,
                font=("Segoe UI", 14, "bold"),
                text_color=ACCENT_CYAN
            ).pack(anchor="w", pady=(0, 10))

            for item in items:
                label_text = item[0]
                setting_key = item[1]
                ctrl_type = item[2]

                row = ctk.CTkFrame(c_inner, fg_color="transparent", height=38)
                row.pack(fill="x", pady=4)

                ctk.CTkLabel(
                    row,
                    text=label_text,
                    font=("Segoe UI", 12),
                    text_color=TEXT_PRIMARY
                ).pack(side="left")

                if ctrl_type == "theme_toggle":
                    cur_theme = self.settings.get("theme", "dark")
                    self.theme_switch_var = ctk.BooleanVar(value=(cur_theme != "light"))
                    sw = ctk.CTkSwitch(
                        row,
                        text="",
                        variable=self.theme_switch_var,
                        progress_color=ACCENT_CYAN,
                        command=lambda: self.set_theme("dark" if self.theme_switch_var.get() else "light")
                    )
                    sw.pack(side="right")

                elif ctrl_type == "menu" and setting_key == "theme":
                    cur_theme = self.settings.get("theme", "dark").capitalize()
                    self.theme_menu_var = ctk.StringVar(value=cur_theme)
                    om = ctk.CTkOptionMenu(
                        row,
                        variable=self.theme_menu_var,
                        values=["Dark", "Light", "System"],
                        width=120,
                        height=32,
                        corner_radius=8,
                        fg_color=PANEL_ELEVATED,
                        button_color=ACCENT_CYAN_SUBTLE,
                        button_hover_color=PANEL_HOVER,
                        text_color=TEXT_PRIMARY,
                        dropdown_fg_color=PANEL_COLOR,
                        dropdown_hover_color=ACCENT_CYAN_SUBTLE,
                        dropdown_text_color=TEXT_PRIMARY,
                        command=lambda val: self.set_theme(val.lower())
                    )
                    om.pack(side="right")

                elif ctrl_type == "switch" and setting_key:
                    sw_var = ctk.BooleanVar(value=bool(self.settings.get(setting_key, False)))
                    sw = ctk.CTkSwitch(
                        row,
                        text="",
                        variable=sw_var,
                        progress_color=ACCENT_CYAN,
                        command=lambda k=setting_key, v=sw_var: self._update_setting(k, v.get())
                    )
                    sw.pack(side="right")

                elif ctrl_type == "menu" and setting_key:
                    options = item[3]
                    current_val = str(self.settings.get(setting_key, options[0]))
                    if current_val not in options:
                        current_val = options[0]
                    om_var = ctk.StringVar(value=current_val)
                    om = ctk.CTkOptionMenu(
                        row,
                        variable=om_var,
                        values=options,
                        width=170 if len(options[0]) > 8 else 120,
                        height=32,
                        corner_radius=8,
                        fg_color=PANEL_ELEVATED,
                        button_color=ACCENT_CYAN_SUBTLE,
                        button_hover_color=PANEL_HOVER,
                        text_color=TEXT_PRIMARY,
                        dropdown_fg_color=PANEL_COLOR,
                        dropdown_hover_color=ACCENT_CYAN_SUBTLE,
                        dropdown_text_color=TEXT_PRIMARY,
                        command=lambda val, k=setting_key: self._update_setting(k, val)
                    )
                    om.pack(side="right")

    def _update_setting(self, key: str, value) -> None:
        self.settings[key] = value
        self._save_settings()
        if key == "default_quality" and hasattr(self, "selected_quality"):
            self.selected_quality.set(str(value))

    # ==========================================
    # VIEW 4: ABOUT (NO SCROLL)
    # ==========================================
    def _init_about_view(self) -> None:
        if "about" in self.views:
            return

        view = ctk.CTkFrame(self.views_container, fg_color="transparent")
        self.views["about"] = view

        about_card = ctk.CTkFrame(
            view,
            fg_color=PANEL_COLOR,
            corner_radius=20,
            border_width=1,
            border_color=BORDER_COLOR
        )
        about_card.pack(fill="both", expand=True, padx=30, pady=16)

        card_inner = ctk.CTkFrame(about_card, fg_color="transparent")
        card_inner.pack(expand=True, padx=30, pady=24)

        logo_row = ctk.CTkFrame(card_inner, fg_color="transparent")
        logo_row.pack(anchor="center")

        ctk.CTkLabel(
            logo_row,
            text="FORTY.",
            font=("Segoe UI", 36, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            logo_row,
            text="FETCH",
            font=("Segoe UI", 36, "bold"),
            text_color=ACCENT_CYAN
        ).pack(side="left")

        ctk.CTkLabel(
            card_inner,
            text="HIGH SPEED YOUTUBE DOWNLOADER",
            font=("Segoe UI", 11, "bold"),
            text_color=ACCENT_CYAN
        ).pack(pady=(2, 6))

        badge = ctk.CTkFrame(card_inner, fg_color=BADGE_BG, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        badge.pack(pady=4)

        ctk.CTkLabel(
            badge,
            text=f"  Version v{APP_VERSION} (Optimized Fast-Launch)  ",
            font=("Consolas", 11, "bold"),
            text_color=TEXT_MUTED
        ).pack(padx=8, pady=3)

        ctk.CTkLabel(
            card_inner,
            text="A lightweight desktop downloader focused on speed, simplicity and reliability.\n"
                 "Engineered with dark and light aesthetics for professional Windows desktop users.",
            font=("Segoe UI", 12),
            text_color=TEXT_MUTED,
            justify="center"
        ).pack(pady=12)

        specs_frame = ctk.CTkFrame(card_inner, fg_color=PANEL_ELEVATED, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        specs_frame.pack(fill="x", pady=(0, 20), padx=20)

        ctk.CTkLabel(
            specs_frame,
            text="Python 3.14  •  CustomTkinter  •  yt-dlp  •  FFmpeg Core  •  Up to 8K 60fps",
            font=("Consolas", 11, "bold"),
            text_color=ACCENT_CYAN
        ).pack(padx=16, pady=8)

        btn_row = ctk.CTkFrame(card_inner, fg_color="transparent")
        btn_row.pack()

        ctk.CTkButton(
            btn_row,
            text="GitHub Repository",
            width=135,
            height=34,
            corner_radius=9,
            fg_color=PANEL_ELEVATED,
            hover_color=PANEL_HOVER,
            border_width=1,
            border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY,
            font=("Segoe UI", 11, "bold"),
            command=lambda: webbrowser.open(GITHUB_URL)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="Discord",
            width=110,
            height=34,
            corner_radius=9,
            fg_color=ACCENT_DISCORD,
            hover_color=ACCENT_DISCORD_HOVER,
            text_color="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            command=lambda: webbrowser.open(DISCORD_URL)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="Check for Updates",
            width=140,
            height=34,
            corner_radius=9,
            fg_color=ACCENT_GREEN_SUBTLE,
            hover_color=ACCENT_GREEN_HOVER,
            border_width=1,
            border_color=ACCENT_GREEN,
            text_color=ACCENT_GREEN,
            font=("Segoe UI", 11, "bold"),
            command=self.start_manual_update_thread
        ).pack(side="left", padx=5)

    # ==========================================
    # DOWNLOAD & BACKEND ENGINE
    # ==========================================
    def select_path(self) -> None:
        path = filedialog.askdirectory(initialdir=self.save_path)
        if path:
            self.save_path = path
            self.folder_display.configure(state="normal")
            self.folder_display.delete(0, "end")
            self.folder_display.insert(0, path)
            self.folder_display.configure(state="disabled")

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

    def _update_download_progress(self, percent: float) -> None:
        p_val = max(0.0, min(100.0, percent))
        self.progress_bar.set(p_val / 100)
        self.percent_label.configure(text=f"{int(p_val)}%")
        self.circular_progress.set_progress(p_val)
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

    def show_update_help(self) -> None:
        pop = ctk.CTkToplevel(self)
        pop.title("Update Help")
        pop.geometry("560x420")
        pop.configure(fg_color=BG_COLOR)
        pop.resizable(False, False)
        self._bring_popup_front(pop)

        ctk.CTkLabel(pop, text="Update Instructions", font=("Segoe UI", 24, "bold"), text_color=ACCENT_CYAN).pack(pady=(20, 10))

        help_text = (
            "1. Click 'Check for Updates' from the top-right header.\n"
            "2. FortyFetch checks yt-dlp, FFmpeg, and FFprobe.\n"
            "3. If updates are available, they are downloaded and installed automatically.\n"
            "4. You will see one of these results:\n"
            "   - Update successful\n"
            "   - No updates available\n\n"
            "Tip: Ensure an active internet connection when checking for updates."
        )
        ctk.CTkLabel(
            pop,
            text=help_text,
            justify="left",
            anchor="w",
            font=("Segoe UI", 13),
            text_color=TEXT_PRIMARY,
        ).pack(fill="both", expand=True, padx=28, pady=(4, 14))

        ctk.CTkButton(
            pop,
            text="Close",
            width=120,
            height=38,
            corner_radius=10,
            fg_color=PANEL_ELEVATED,
            hover_color=PANEL_HOVER,
            border_width=1,
            border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY,
            font=("Segoe UI", 13, "bold"),
            command=pop.destroy,
        ).pack(pady=(0, 20))

    # ==========================================
    # THROTTLED HIGH-PERFORMANCE PROGRESS HOOK
    # ==========================================
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

    def show_donation_info(self) -> None:
        pop = ctk.CTkToplevel(self)
        pop.title("Buy Me a Coffee")
        pop.geometry("460x620")
        pop.configure(fg_color=BG_COLOR)
        pop.resizable(False, False)
        self._bring_popup_front(pop)

        ctk.CTkLabel(
            pop,
            text="Buy me a Coffee",
            font=("Segoe UI", 28, "bold"),
            text_color=ACCENT_CYAN
        ).pack(pady=(20, 10))

        qr_path = os.path.join(self.assets_dir, "qr_code.png")
        if os.path.exists(qr_path):
            try:
                # Cache decoded image object in memory so reopening is instant
                if self._qr_image_cached is None:
                    from PIL import Image
                    img_data = Image.open(qr_path)
                    self._qr_image_cached = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(300, 300))
                qr_label = ctk.CTkLabel(pop, image=self._qr_image_cached, text="")
                qr_label.image = self._qr_image_cached
                qr_label.pack(pady=8)
            except Exception:
                ctk.CTkLabel(pop, text="Unable to load QR image.", text_color="#FF6B6B", font=("Segoe UI", 14)).pack()
        else:
            ctk.CTkLabel(pop, text="QR code not found in assets.", text_color="#FF6B6B", font=("Segoe UI", 14)).pack()

        ctk.CTkLabel(
            pop,
            text=f"UPI: {UPI_ID}",
            font=("Segoe UI", 16, "bold"),
            text_color=ACCENT_CYAN
        ).pack(pady=(8, 4))

        ctk.CTkButton(
            pop,
            text="PayPal Me",
            width=200,
            height=38,
            corner_radius=10,
            fg_color="#003087",
            hover_color="#0079C1",
            text_color="#FFFFFF",
            font=("Segoe UI", 13, "bold"),
            command=lambda: webbrowser.open(PAYPAL_URL),
        ).pack(pady=(8, 14))

        ctk.CTkButton(
            pop,
            text="Close",
            width=120,
            height=38,
            corner_radius=10,
            fg_color=PANEL_ELEVATED,
            hover_color=PANEL_HOVER,
            border_width=1,
            border_color=BORDER_COLOR,
            text_color=TEXT_PRIMARY,
            font=("Segoe UI", 13),
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
    try:
        app = FortyFetchApp()
        app.mainloop()
    except Exception:
        import traceback as _tb
        err = _tb.format_exc()
        try:
            log_path = os.path.join(
                os.path.dirname(sys.executable if is_frozen_build() else __file__),
                "FortyFetch_crash.log",
            )
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(err)
        except Exception:
            log_path = "unknown"
        try:
            from tkinter import messagebox as _mb
            _mb.showerror("FortyFetch - Crash", f"Fatal error:\n{err}\n\nLog: {log_path}")
        except Exception:
            pass
        sys.exit(1)
