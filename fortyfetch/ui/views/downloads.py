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

class DownloadsViewMixin:
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

