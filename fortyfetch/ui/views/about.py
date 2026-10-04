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

class AboutViewMixin:
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

