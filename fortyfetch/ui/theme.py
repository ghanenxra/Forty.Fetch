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

class ThemeMixin:
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

