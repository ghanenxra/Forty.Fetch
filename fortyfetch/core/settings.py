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

class SettingsMixin:
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

        def _update_setting(self, key: str, value) -> None:
            self.settings[key] = value
            self._save_settings()
            if key == "default_quality" and hasattr(self, "selected_quality"):
                self.selected_quality.set(str(value))

