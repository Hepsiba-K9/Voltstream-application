# VoltStream

React + FastAPI reference application for prosumer energy monitoring.

This build includes the VoltStream frontend and FastAPI backend:

- Live dashboard
- Usage analytics
- Smart device controls
- Billing summary
- Gemini energy chat
- ChromaDB-backed grounded document Q&A
- 404 fallback

## Gemini Setup

Create a project-root `.env` file before using the assistant:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and replace `your_gemini_api_key_here` with your Gemini API key.
The default chat model is:

```env
GEMINI_MODEL=models/gemini-2.5-flash
```

## Run Backend

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd backend
uvicorn main:app --reload
```

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend dev server proxies API calls to `http://localhost:8000`.

Open the app at `http://localhost:5175`.

Frontend stack: ReactJS, React Router, Tailwind CSS, Recharts, and Lucide React.
Backend stack: FastAPI, Uvicorn, Pydantic, ChromaDB, Gemini, and CORS middleware.

Backend layout:

- `backend/main.py` creates the FastAPI app.
- `backend/api.py` contains all API endpoints.
- `backend/ai_service.py` contains Gemini chat and document Q&A logic.
- `backend/database.py` creates tables, reads data, and writes new data in the local SQLite database.
- `backend/data_models.py` contains Pydantic response models.
- `backend/data/energy_efficiency_guide.txt`, `backend/data/energy_efficiency_report.txt`, and `backend/data/detailed_energy_efficiency_report.txt` are the included Q&A reference documents.

SQLite storage:

- Runtime data is stored in `backend/databases/voltstream.sqlite3` by default.
- Set `VOLTSTREAM_DB_PATH` in `.env` to use a different database file.
- Dashboard, usage history, devices, and billing data are read from SQLite. New device and billing updates are written back to SQLite.
- The React frontend does not open SQLite directly. It calls FastAPI endpoints, and FastAPI reads/analyzes the SQLite data for cards and graphs.

Assistant endpoints:

- `POST /api/v1/chat` runs the normal Gemini chat bot.
- `POST /api/v1/qa` runs the RAG Q&A bot against the reference documents in `backend/data/`.
- `GET /api/v1/qa/document` returns the indexed document status.
- Local document embeddings and ChromaDB files are persisted under `backend/databases/chroma_store/`.
