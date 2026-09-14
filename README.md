# BuildPulse (minimal scaffold)

This workspace contains a minimal scaffold for the BuildPulse demo:

- `backend/app/main.py` — FastAPI app with `/health` endpoint
- `frontend/app.py` — Streamlit placeholder
- `docker-compose.yml` — local compose with Postgres, api, frontend
- `.env.example` — environment variables

Quick local checks (Windows PowerShell):

```powershell
cd "C:\Users\Vijay\OneDrive\Documents\HACK"
# activate venv
.\.venv\Scripts\Activate.ps1
# run backend (uvicorn)
.\.venv\Scripts\python -m uvicorn backend.app.main:app --port 8000 --reload
# run frontend (streamlit)
.\.venv\Scripts\streamlit run frontend\app.py
```

You can also run `docker compose up --build` if you create Dockerfiles.
