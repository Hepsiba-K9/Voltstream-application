# VoltStream

React + FastAPI reference application for prosumer energy monitoring.

This build includes the Week 1 style frontend and backend only:

- Live dashboard
- Usage analytics
- Smart device controls
- Billing summary
- 404 fallback

AI chat, QA, and agent endpoints are intentionally not included.

## Run Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend expects the API at `http://localhost:8000`.

Open the app at `http://localhost:5175`.

Frontend stack: ReactJS, React Router, Tailwind CSS, Recharts, and Lucide React.
Backend stack: FastAPI, Uvicorn, Pydantic, and CORS middleware.

Backend layout:

- `backend/main.py` creates the FastAPI app.
- `backend/api.py` contains all API endpoints.
- `backend/mockdata.py` contains mock database values.
- `backend/data_models.py` contains Pydantic response models.
