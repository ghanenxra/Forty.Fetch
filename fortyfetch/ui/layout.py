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

class LayoutMixin:
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

