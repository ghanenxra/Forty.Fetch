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

class SettingsViewMixin:
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

