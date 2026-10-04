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