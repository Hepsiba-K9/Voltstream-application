# VoltStream

React + FastAPI reference application for prosumer energy monitoring.

This build includes the VoltStream frontend and FastAPI backend:

- Live dashboard
- Usage analytics
- Smart device controls
- Billing summary
- Vertex AI Gemini energy chat
- ChromaDB-backed grounded document Q&A
- 404 fallback

## Deployed Links

- Frontend: https://voltstream-project-95144.web.app
- Backend: https://voltstream-backend-335699237868.us-central1.run.app
- Backend health check: https://voltstream-backend-335699237868.us-central1.run.app/health

## Vertex AI Gemini Setup

Create a project-root `.env` file before using the assistant:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` with your Google Cloud project and local credentials path:

```env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=voltstreamapp
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
GEMINI_MODEL=gemini-2.5-flash
```

Do not commit service account JSON files. If a key has been shared or pasted anywhere, delete that key in Google Cloud IAM and create a new one before using it.

The default chat model is:

```env
GEMINI_MODEL=gemini-2.5-flash
```

For local Gemini API-key development, you can instead set `GEMINI_API_KEY`, but Vertex AI is the preferred setup for this app.

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
Backend stack: FastAPI, Uvicorn, Pydantic, ChromaDB, Vertex AI Gemini, and CORS middleware.

Backend layout:

- `backend/main.py` creates the FastAPI app.
- `backend/api.py` contains all API endpoints.
- `backend/ai_service.py` contains Gemini chat and document Q&A logic.
- `backend/database.py` creates tables, reads data, and writes new data through SQLite locally or Cloud SQL MySQL in deployment.
- `backend/data_models.py` contains Pydantic response models.
- `backend/data/energy_efficiency_guide.txt`, `backend/data/energy_efficiency_report.txt`, and `backend/data/detailed_energy_efficiency_report.txt` are the included Q&A reference documents.

Database storage:

- Local runtime data is stored in `backend/databases/voltstream.sqlite3` by default.
- Cloud deployment uses Cloud SQL MySQL when `DATABASE_ENGINE=mysql` and Cloud SQL environment variables are set.
- Dashboard, usage history, devices, and billing data are read through FastAPI. New device and billing updates are written back to the configured database.
- The React frontend does not open the database directly. It calls FastAPI endpoints, and FastAPI reads/analyzes the database data for cards and graphs.

Assistant endpoints:

- `POST /api/v1/chat` runs the normal Gemini chat bot.
- `POST /api/v1/qa` runs the RAG Q&A bot against the reference documents in `backend/data/`.
- `GET /api/v1/qa/document` returns the indexed document status.
- Local document embeddings and ChromaDB files are persisted under `backend/databases/chroma_store/`.
