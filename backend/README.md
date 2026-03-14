# FortyFetch Backend

## Run

```powershell
cd "SEM I/FortyFetch/backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Notes

- Set `FORTYFETCH_FFMPEG_LOCATION` to a folder containing `ffmpeg` and `ffprobe` if needed.
- API endpoints:
  - `POST /downloads`
  - `GET /downloads/{job_id}`
  - `GET /downloads/{job_id}/file`
