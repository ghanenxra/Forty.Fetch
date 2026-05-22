import os
import sys
import shutil
import subprocess
import threading
import time
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Colors - Modern professional setup wizard theme
ACCENT_COLOR = "#3B82F6"
ACCENT_HOVER = "#2563EB"
BG_COLOR = "#0F172A"
CARD_COLOR = "#1E293B"
INPUT_COLOR = "#0F172A"
TEXT_MUTED = "#94A3B8"
TEXT_LIGHT = "#F8FAFC"

APP_NAME = "FortyFetch"
DEFAULT_INSTALL_DIR = os.path.normpath(
    os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Local")),
        APP_NAME
    )
)


def get_source_exe() -> str:
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.dirname(os.path.realpath(__file__))

    candidate = os.path.join(base_path, "FortyFetch.exe")
    if os.path.exists(candidate):
        return candidate

    # Dev fallback
    dev_candidate = os.path.join(base_path, "dist", "FortyFetch.exe")
    if os.path.exists(dev_candidate):
        return dev_candidate

    return ""


def create_shortcut(target_path: str, shortcut_path: str) -> None:
    target_path = os.path.abspath(target_path)
    shortcut_path = os.path.abspath(shortcut_path)
    powershell_cmd = (
        f"$WshShell = New-Object -ComObject WScript.Shell; "
        f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path}'); "
        f"$Shortcut.TargetPath = '{target_path}'; "
        f"$Shortcut.WorkingDirectory = '{os.path.dirname(target_path)}'; "
        f"$Shortcut.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", powershell_cmd],
        creationflags=subprocess.CREATE_NO_WINDOW
    )


def run_silent_install() -> int:
    try:
        # Silently kill FortyFetch if running
        subprocess.run(
            ["taskkill", "/F", "/IM", "FortyFetch.exe"],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(1)

        src_exe = get_source_exe()
        if not src_exe:
            return 1

        os.makedirs(DEFAULT_INSTALL_DIR, exist_ok=True)
        dest_exe = os.path.join(DEFAULT_INSTALL_DIR, "FortyFetch.exe")
        shutil.copy2(src_exe, dest_exe)

        # Create shortcuts by default in silent mode
        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        desktop_dir = os.path.join(user_profile, "Desktop")
        start_menu_dir = os.path.join(
            os.environ.get("APPDATA", os.path.join(user_profile, "AppData", "Roaming")),
            "Microsoft", "Windows", "Start Menu", "Programs"
        )

        if os.path.exists(desktop_dir):
            create_shortcut(dest_exe, os.path.join(desktop_dir, f"{APP_NAME}.lnk"))
        if os.path.exists(start_menu_dir):
            create_shortcut(dest_exe, os.path.join(start_menu_dir, f"{APP_NAME}.lnk"))

        return 0
    except Exception:
        return 1


class InstallerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("dark")
        self.title("FortyFetch Setup")
        self.geometry("620x420")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        self.install_dir = DEFAULT_INSTALL_DIR
        self.src_exe = get_source_exe()

        self.desktop_var = ctk.BooleanVar(value=True)
        self.start_menu_var = ctk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self) -> None:
        # Header banner
        header_frame = ctk.CTkFrame(self, fg_color=CARD_COLOR, height=80, corner_radius=0)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text="FortyFetch Installation Setup",
            font=("Segoe UI", 22, "bold"),
            text_color=TEXT_LIGHT,
        ).pack(anchor="w", padx=24, pady=(24, 0))

        # Main Area
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=24, pady=20)

        # Welcome Text
        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text="This wizard will install FortyFetch on your computer.\n\n"
                 "It is recommended to close all other applications before continuing.",
            font=("Segoe UI", 13),
            justify="left",
            text_color="#CBD5E1"
        )
        self.info_label.pack(anchor="w", pady=(5, 10))

        # Path Card
        self.path_card = ctk.CTkFrame(self.main_frame, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color="#334155")
        self.path_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            self.path_card,
            text="Destination Folder:",
            font=("Segoe UI", 12, "bold"),
            text_color=TEXT_LIGHT
        ).pack(anchor="w", padx=16, pady=(10, 2))

        path_row = ctk.CTkFrame(self.path_card, fg_color="transparent")
        path_row.pack(fill="x", padx=16, pady=(0, 12))

        self.path_entry = ctk.CTkEntry(
            path_row,
            height=36,
            fg_color=INPUT_COLOR,
            border_color="#475569",
            text_color="#F8FAFC",
            font=("Segoe UI", 12)
        )
        self.path_entry.insert(0, self.install_dir)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            path_row,
            text="Browse...",
            width=90,
            height=36,
            fg_color="#334155",
            hover_color="#475569",
            text_color=TEXT_LIGHT,
            font=("Segoe UI", 12, "bold"),
            command=self.browse_folder
        )
        self.browse_btn.pack(side="right")

        # Options Card
        self.options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.options_frame.pack(fill="x", pady=5)

        self.desktop_chk = ctk.CTkCheckBox(
            self.options_frame,
            text="Create Desktop Shortcut",
            variable=self.desktop_var,
            font=("Segoe UI", 12),
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER
        )
        self.desktop_chk.pack(side="left", padx=(0, 20))

        self.start_menu_chk = ctk.CTkCheckBox(
            self.options_frame,
            text="Create Start Menu Shortcut",
            variable=self.start_menu_var,
            font=("Segoe UI", 12),
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER
        )
        self.start_menu_chk.pack(side="left")

        # Bottom Action Row
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.bottom_frame.pack(fill="x", side="bottom", padx=24, pady=16)

        self.cancel_btn = ctk.CTkButton(
            self.bottom_frame,
            text="Cancel",
            width=100,
            height=38,
            fg_color="#334155",
            hover_color="#475569",
            text_color=TEXT_LIGHT,
            font=("Segoe UI", 12, "bold"),
            command=self.destroy
        )
        self.cancel_btn.pack(side="right")

        self.install_btn = ctk.CTkButton(
            self.bottom_frame,
            text="Install",
            width=120,
            height=38,
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color="#0F172A",
            font=("Segoe UI", 12, "bold"),
            command=self.start_installation
        )
        self.install_btn.pack(side="right", padx=(0, 12))

        # Progress elements (hidden initially)
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            height=12,
            corner_radius=8,
            fg_color="#0F172A",
            progress_color=ACCENT_COLOR
        )
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Segoe UI", 12, "italic"),
            text_color=TEXT_MUTED
        )

    def browse_folder(self) -> None:
        selected_dir = filedialog.askdirectory(initialdir=self.install_dir)
        if selected_dir:
            self.install_dir = os.path.normpath(selected_dir)
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, self.install_dir)

    def start_installation(self) -> None:
        entered_path = self.path_entry.get().strip()
        if entered_path:
            self.install_dir = os.path.normpath(entered_path)

        if not self.src_exe or not os.path.exists(self.src_exe):
            messagebox.showerror(
                "Error",
                "Source FortyFetch.exe not found! Please build the app executable first."
            )
            return

        self.install_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")
        self.desktop_chk.configure(state="disabled")
        self.start_menu_chk.configure(state="disabled")

        # Swap view: Hide paths and options, show progress
        self.info_label.configure(text="Installing FortyFetch on your computer...")
        self.path_card.pack_forget()  # hide path card
        self.options_frame.pack_forget()  # hide options

        self.progress_bar.pack(fill="x", pady=(40, 10))
        self.progress_label.pack(anchor="w")

        threading.Thread(target=self.run_install_thread, daemon=True).start()

    def run_install_thread(self) -> None:
        steps = [
            ("Closing running instances...", 0.15),
            ("Creating directories...", 0.35),
            ("Extracting application files...", 0.65),
            ("Creating system shortcuts...", 0.85),
            ("Finalizing setup...", 1.0)
        ]

        for desc, progress in steps:
            self.after(0, lambda d=desc, p=progress: self._update_progress(d, p))
            time.sleep(0.6)

            if desc.startswith("Closing"):
                subprocess.run(
                    ["taskkill", "/F", "/IM", "FortyFetch.exe"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            elif desc.startswith("Creating directories"):
                os.makedirs(self.install_dir, exist_ok=True)
            elif desc.startswith("Extracting"):
                dest_exe = os.path.join(self.install_dir, "FortyFetch.exe")
                try:
                    shutil.copy2(self.src_exe, dest_exe)
                except Exception as e:
                    self.after(0, lambda err=e: self._install_error(err))
                    return
            elif desc.startswith("Creating system shortcuts"):
                dest_exe = os.path.join(self.install_dir, "FortyFetch.exe")
                user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))

                if self.desktop_var.get():
                    desktop_dir = os.path.join(user_profile, "Desktop")
                    if os.path.exists(desktop_dir):
                        create_shortcut(dest_exe, os.path.join(desktop_dir, f"{APP_NAME}.lnk"))

                if self.start_menu_var.get():
                    start_menu_dir = os.path.join(
                        os.environ.get("APPDATA", os.path.join(user_profile, "AppData", "Roaming")),
                        "Microsoft", "Windows", "Start Menu", "Programs"
                    )
                    if os.path.exists(start_menu_dir):
                        create_shortcut(dest_exe, os.path.join(start_menu_dir, f"{APP_NAME}.lnk"))

        self.after(0, self._install_finished)

    def _update_progress(self, desc: str, progress: float) -> None:
        self.progress_label.configure(text=desc)
        self.progress_bar.set(progress)

    def _install_error(self, err: Exception) -> None:
        messagebox.showerror("Installation Failed", f"An error occurred: {err}")
        self.destroy()

    def _install_finished(self) -> None:
        self.info_label.configure(text="Installation completed successfully!")
        self.progress_bar.pack_forget()
        self.progress_label.configure(
            text="FortyFetch has been installed. Click 'Launch' to start the application.",
            font=("Segoe UI", 13)
        )

        self.cancel_btn.configure(text="Close", state="normal")
        self.install_btn.configure(
            text="Launch",
            state="normal",
            command=self.launch_app
        )

    def launch_app(self) -> None:
        dest_exe = os.path.join(self.install_dir, "FortyFetch.exe")
        if os.path.exists(dest_exe):
            try:
                subprocess.Popen([dest_exe])
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    # Check command-line arguments for silent installation
    args = [arg.upper() for arg in sys.argv[1:]]
    if "/VERYSILENT" in args or "/SILENT" in args:
        code = run_silent_install()
        sys.exit(code)

    app = InstallerApp()
    app.mainloop()
