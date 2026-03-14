# FortyFetch Android Starter

## 1) Open in Android Studio

Open folder:

`SEM I/FortyFetch/android`

## 2) Sync Gradle

Let Android Studio install requested SDK/Gradle plugins.

## 3) Start backend first

Run backend from:

`SEM I/FortyFetch/backend`

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4) Set backend URL in app

In `app/src/main/java/com/fortyfetch/mobile/MainActivity.kt`, update `BASE_URL`:

- Android emulator to same PC: `http://10.0.2.2:8000/`
- Physical phone on same Wi-Fi: `http://<YOUR_PC_LAN_IP>:8000/`

## 5) Run app

Pick emulator/phone and run.

## 6) Current scope

This starter supports:
- URL input
- Quality selection
- Start download
- Polling progress/status

File download-to-phone is the next step (currently backend keeps files on server).
