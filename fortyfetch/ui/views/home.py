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

class HomeViewMixin:
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

            # Toggle Row for Console Mode
            toggle_row = ctk.CTkFrame(view, fg_color="transparent")
            toggle_row.pack(fill="x", pady=(4, 2), padx=4)
            
            self.console_mode_var = ctk.BooleanVar(value=False)
            self.console_toggle = ctk.CTkSwitch(
                toggle_row,
                text="Console Mode",
                command=self.toggle_console_mode,
                variable=self.console_mode_var,
                font=("Consolas", 11, "bold"),
                text_color=TEXT_MUTED,
                onvalue=True,
                offvalue=False,
                progress_color=ACCENT_CYAN,
                switch_width=36,
                switch_height=18
            )
            self.console_toggle.pack(side="right")

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

            # 4.5 Console Card
            self.console_card = ctk.CTkFrame(
                view,
                fg_color="#000000",
                corner_radius=12,
                border_width=1,
                border_color="#333333"
            )
            # Mac-like header
            c_header = ctk.CTkFrame(self.console_card, fg_color="#1E1E1E", corner_radius=12, height=28)
            c_header.pack(fill="x", side="top")
            
            # macOS traffic lights
            dots = ctk.CTkFrame(c_header, fg_color="transparent")
            dots.pack(side="left", padx=12, pady=6)
            ctk.CTkFrame(dots, width=12, height=12, corner_radius=6, fg_color="#FF5F56").pack(side="left", padx=3)
            ctk.CTkFrame(dots, width=12, height=12, corner_radius=6, fg_color="#FFBD2E").pack(side="left", padx=3)
            ctk.CTkFrame(dots, width=12, height=12, corner_radius=6, fg_color="#27C93F").pack(side="left", padx=3)

            ctk.CTkLabel(c_header, text="bash — fortyfetch-engine", font=("Consolas", 10), text_color="#888888").place(relx=0.5, rely=0.5, anchor="center")

            self.console_text = ctk.CTkTextbox(
                self.console_card,
                fg_color="#000000",
                text_color="#00FF00",
                font=("Consolas", 11),
                height=160,
                wrap="word"
            )
            self.console_text.pack(fill="both", expand=True, padx=8, pady=8)
            self.console_text.insert("0.0", "fortyfetch@engine:~$ Ready for commands...\n")
            self.console_text.configure(state="disabled")

            # 5. Bottom Actions Row
            self.footer_row = ctk.CTkFrame(view, fg_color="transparent")
            self.footer_row.pack(fill="x", pady=(2, 0))

            ctk.CTkButton(
                self.footer_row,
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
                self.footer_row,
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
                self.footer_row,
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
                self.footer_row,
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

        def select_path(self) -> None:
            path = filedialog.askdirectory(initialdir=self.save_path)
            if path:
                self.save_path = path
                self.folder_display.configure(state="normal")
                self.folder_display.delete(0, "end")
                self.folder_display.insert(0, path)
                self.folder_display.configure(state="disabled")

        def _bring_popup_front(self, pop: ctk.CTkToplevel) -> None:
            pop.transient(self)
            pop.lift()
            pop.attributes("-topmost", True)
            pop.after(250, lambda: pop.attributes("-topmost", False))
            pop.focus_force()

        def toggle_console_mode(self) -> None:
            if self.console_mode_var.get():
                self.progress_card.pack_forget()
                self.console_card.pack(fill="x", pady=(0, 10), before=self.footer_row.master.winfo_children()[-1])
            else:
                self.console_card.pack_forget()
                self.progress_card.pack(fill="x", pady=(0, 10), before=self.footer_row.master.winfo_children()[-1])


