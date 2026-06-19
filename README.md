# 🔌 VoltStream - Smart Energy Monitoring System

**VoltStream** is a smart energy monitoring application that helps homeowners track, analyze, and control their electricity usage in real-time. It connects to your solar panels, smart devices, and shows you how to save money on your electricity bill.

---

## 🌍 Live Deployment Status

### **✅ Currently Deployed Online**

| Component | Status | URL | Provider |
|-----------|--------|-----|----------|
| **Frontend (Website)** | 🟢 Live | [voltstream-project-95144.web.app](https://voltstream-project-95144.web.app) | 🔥 Firebase Hosting |
| **Backend (API)** | 🟢 Live | [voltstream-backend-335699237868.us-central1.run.app](https://voltstream-backend-335699237868.us-central1.run.app) | ☁️ Google Cloud Run |
| **Database** | 🟢 Active | 35.202.131.68:3306 | ☁️ Cloud SQL (MySQL) |
| **AI Engine** | 🟢 Active | Vertex AI Gemini | ☁️ Google Cloud Platform |
| **Document Search** | 🟢 Active | ChromaDB | ☁️ Cloud Storage |

### **🖥️ Local Development**

Run locally at:
- **Frontend**: `http://localhost:5173` (React Dev Server)
- **Backend**: `http://localhost:8000` (FastAPI Server)
- **Database**: SQLite in `backend/databases/`

---

## ⚡ What Can You Do With VoltStream?

1. **📊 Live Dashboard** - See how much electricity you're using RIGHT NOW
2. **📈 Usage Analytics** - Track your daily, weekly, and monthly electricity consumption
3. **🏠 Smart Device Control** - Turn devices on/off remotely (lights, AC, water heater, etc.)
4. **💰 Billing Summary** - See your electricity costs and set budget limits
5. **🤖 AI Energy Assistant** - Ask questions like "How can I save energy?" and get smart recommendations
6. **☀️ Solar Integration** - View solar generation vs. grid usage
7. **📚 Energy Learning** - Get answers about energy efficiency from expert documents
8. **🔋 Battery Management** - Monitor and optimize battery charging/discharging

---

## 🛠️ Technology Stack

### **Frontend Stack** (What You See)

| Technology | What It Does |
|-----------|-------------|
| **React 18** | Makes the website interactive |
| **Vite** | Fast build tool (loads super quick) |
| **React Router** | Navigation between pages |
| **Tailwind CSS** | Beautiful styling & design |
| **Recharts** | Creates graphs & charts |
| **Lucide React** | Icons & symbols |

### **Backend Stack** (The Brain)

| Technology | What It Does |
|-----------|-------------|
| **FastAPI** | Web server that handles requests |
| **Python 3.10+** | Programming language |
| **Uvicorn** | Runs the FastAPI server |
| **SQLite** | Local database (your computer) |
| **Cloud SQL MySQL** | Cloud database (online) |
| **Vertex AI Gemini** | Google's AI engine |
| **ChromaDB** | AI-powered document search |
| **Pydantic** | Data validation |

### **Google Cloud Services Used**

| Service | Purpose | Region |
|---------|---------|--------|
| **Cloud Run** | Runs the backend server | us-central1 |
| **Vertex AI** | Powers Gemini AI | us-central1 |
| **Cloud SQL MySQL** | Stores all data | us-central1 |
| **Firebase Hosting** | Hosts the website | Global CDN |
| **Cloud Storage** | Stores documents & embeddings | us-central1 |

---

## � Deployment Architecture

### **Where Things Run**

| Component | Technology | Location | Link |
|-----------|-----------|----------|------|
| **Frontend** | React + Vite | 🔥 **Firebase Hosting** | [voltstream-project-95144.web.app](https://voltstream-project-95144.web.app) |
| **Backend** | FastAPI + Python | ☁️ **Google Cloud Run** | [voltstream-backend-335699237868.us-central1.run.app](https://voltstream-backend-335699237868.us-central1.run.app) |
| **Database** | Cloud SQL MySQL | ☁️ **Google Cloud** | 35.202.131.68:3306 |
| **AI Engine** | Vertex AI Gemini | ☁️ **Google Cloud** | us-central1 |
| **Document Search** | ChromaDB | ☁️ **Google Cloud Storage** | Embedded in backend |

### **How Frontend & Backend Talk**

```
┌─────────────────────────────────┐
│     Firebase (Frontend)          │
│  https://voltstream-...web.app   │
│  (React Dashboard)               │
└────────────┬────────────────────┘
             │ HTTPS Requests
             ▼
┌─────────────────────────────────┐
│  Google Cloud Run (Backend)      │
│  .../api/v1/...                  │
│  (FastAPI Server)                │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┬──────────┬─────────┐
    ▼                 ▼          ▼         ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐
│ Cloud   │  │ Vertex   │  │ ChromaDB │  │ Cloud   │
│ SQL     │  │ AI       │  │ Search   │  │ Storage │
│ MySQL   │  │ Gemini   │  │ Index    │  │ Files   │
└─────────┘  └──────────┘  └──────────┘  └─────────┘
```

---

## 📦 Project Structure (Detailed Breakdown)

### **📁 Backend Folder** (`backend/` - FastAPI Server)

| File/Folder | Purpose | Language |
|------------|---------|----------|
| `main.py` | Starts FastAPI server & loads database | Python |
| `api.py` | All REST API endpoints (`/api/v1/`) | Python |
| `ai_service.py` | Chat & Document Q&A logic | Python |
| `database.py` | SQLite/MySQL read/write operations | Python |
| `data_models.py` | Pydantic data structure definitions | Python |
| `requirements.txt` | All Python packages needed | Text |
| `Dockerfile` | Build backend for Google Cloud | Docker |
| `voltstreamapp-*.json` | Google Cloud credentials ⚠️ SECRET | JSON |

**Subdirectories:**

| Folder | What's Inside | Purpose |
|--------|---------------|---------|
| `agents/` | `evaluation.py`, `orchestrator_agent.py`, `advisor_agent.py` | AI agents that process requests |
| `ai_services/` | `chat_service.py`, `document_qa_service.py`, `embedding_service.py` | AI helper functions |
| `data/` | `energy_efficiency_guide.txt`, `energy_efficiency_report.txt`, `detailed_energy_efficiency_report.txt` | Reference documents for AI Q&A |
| `databases/` | `voltstream.sqlite3`, `chroma_store/` | Local data storage (SQLite) + AI search index |

---

### **📁 Frontend Folder** (`frontend/` - React Website)

| File/Folder | Purpose | Language |
|------------|---------|----------|
| `package.json` | NPM packages & commands | JSON |
| `index.html` | Main HTML file | HTML |
| `vite.config.js` | Vite build configuration | JavaScript |
| `tailwind.config.js` | Tailwind CSS styling | JavaScript |
| `postcss.config.js` | CSS processing config | JavaScript |
| `firebase.json` | Firebase deployment config | JSON |
| `nginx.conf` | Web server configuration | Config |

**Subdirectories:**

| Folder | What's Inside | Purpose |
|--------|---------------|---------|
| `src/` | `main.jsx`, `api.js`, `styles.css` | React source code |
| `src/components/` | Page components | Website pages |
| `src/ui/` | Reusable UI elements | Buttons, cards, etc |
| `src/assets/` | Images & icons | Visual files |
| `public/` | Static files | Served as-is |

**Frontend Components:**

| Component | Purpose | Shows |
|-----------|---------|-------|
| `LiveDashboard.jsx` | Real-time electricity view | Current kW usage |
| `UsageHistory.jsx` | Daily/weekly/monthly charts | Consumption trends |
| `SmartControl.jsx` | Device on/off control | Connected devices |
| `Invoices.jsx` | Billing & costs | Bill amount & budget |
| `AIAssistant.jsx` | Chat with energy bot | Smart advice |
| `FloatingAssistant.jsx` | Mini AI chat button | Quick access |
| `DeviceAgent.jsx` | Device management | Add/remove devices |

---

### **📁 Root Folder Files**

| File | Purpose | Type |
|------|---------|------|
| `.env` | Your Google Cloud config (SECRET) | Config |
| `.env.example` | Template for `.env` | Config |
| `.gitignore` | Don't upload these files | Config |
| `README.md` | This file! | Markdown |
| `start_backend.bat` | Quick start backend (Windows) | Batch |
| `start_voltstream.bat` | Start everything (Windows) | Batch |
| `docker-compose.yml` | Run everything in Docker | Docker |

---

## 📊 Complete File Tree

```
voltstream_application/
│
├── 🔙 BACKEND (Google Cloud Run)
│   └── backend/
│       ├── main.py                           # Entry point
│       ├── api.py                            # REST endpoints
│       ├── ai_service.py                     # AI logic
│       ├── database.py                       # Database operations
│       ├── data_models.py                    # Data structures
│       ├── requirements.txt                  # Python packages
│       ├── Dockerfile                        # Docker build
│       │
│       ├── agents/                           # AI decision makers
│       │   ├── __init__.py
│       │   ├── evaluation.py                 # Tests AI answers
│       │   ├── orchestrator_agent.py         # Routes requests
│       │   ├── advisor_agent.py              # Energy advice
│       │   ├── analyst_agent.py              # Data analysis
│       │   ├── device_agent.py               # Device control
│       │   ├── runner_agent.py               # Execution
│       │   ├── comments.py                   # Prompts
│       │   └── tools.py                      # Helper tools
│       │
│       ├── ai_services/                      # AI helpers
│       │   ├── __init__.py
│       │   ├── ai_common.py                  # Gemini setup
│       │   ├── chat_service.py               # Chat logic
│       │   ├── document_qa_service.py        # Document search
│       │   ├── embedding_service.py          # Vector search
│       │   └── text_chunker.py               # Document splitting
│       │
│       ├── data/                             # Reference documents
│       │   ├── energy_efficiency_guide.txt
│       │   ├── energy_efficiency_report.txt
│       │   └── detailed_energy_efficiency_report.txt
│       │
│       ├── databases/                        # Data storage
│       │   ├── voltstream.sqlite3            # Local data
│       │   └── chroma_store/                 # Search index
│       │
│       └── voltstreamapp-*.json              # ⚠️ CREDENTIALS
│
├── 🌐 FRONTEND (Firebase Hosting)
│   └── frontend/
│       ├── package.json                      # Node packages
│       ├── index.html                        # Main HTML
│       ├── vite.config.js                    # Build config
│       ├── tailwind.config.js                # Styling config
│       ├── postcss.config.js                 # CSS config
│       ├── firebase.json                     # Firebase config
│       ├── nginx.conf                        # Web server config
│       │
│       ├── src/
│       │   ├── main.jsx                      # React entry
│       │   ├── api.js                        # API calls
│       │   ├── styles.css                    # Global styles
│       │   │
│       │   ├── components/                   # Page components
│       │   │   ├── LiveDashboard.jsx         # Real-time view
│       │   │   ├── UsageHistory.jsx          # Charts & trends
│       │   │   ├── SmartControl.jsx          # Device control
│       │   │   ├── Invoices.jsx              # Billing info
│       │   │   ├── AIAssistant.jsx           # Chat window
│       │   │   ├── FloatingAssistant.jsx     # Chat button
│       │   │   ├── DeviceAgent.jsx           # Device manager
│       │   │   └── NotFound.jsx              # 404 page
│       │   │
│       │   ├── ui/                           # Reusable UI
│       │   │   ├── AppShell.jsx              # App layout
│       │   │   └── State.jsx                 # State management
│       │   │
│       │   └── assets/                       # Images & icons
│       │
│       └── public/                           # Static files
│           └── images/
│
├── 🛠️ CONFIG & SCRIPTS (Root)
│   ├── .env                                  # Your config ⚠️
│   ├── .env.example                          # Config template
│   ├── .gitignore                            # Git ignore rules
│   ├── README.md                             # Documentation
│   ├── start_backend.bat                     # Quick start
│   ├── start_voltstream.bat                  # Start all
│   └── docker-compose.yml                    # Docker setup
│
└── 📚 SCRIPTS (Optional)
    └── scripts/
        ├── create_week5_task_doc.py
        └── show_agent_evaluation.py
```

---

## 🚀 Quick Start (For Beginners)

---

## 🚀 Quick Start (For Beginners)

### **Step 1: Download and Install Python**

- Download [Python 3.10+](https://www.python.org/downloads/)
- During installation, check ✅ "Add Python to PATH"

### **Step 2: Download This Project**

```bash
git clone https://github.com/your-repo/voltstream_application.git
cd voltstream_application
```

### **Step 3: Setup Google Cloud (For AI Features)**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project called "VoltStream"
3. Enable these services:
   - ✅ Vertex AI API
   - ✅ Cloud Storage API
4. Create a service account:
   - Go to **IAM & Admin** → **Service Accounts**
   - Click **Create Service Account**
   - Name it "voltstream"
   - Grant it **Vertex AI Administrator** role
   - Create a **JSON key** and download it

### **Step 4: Create `.env` File**

In the project root folder, create a file called `.env`:

```env
# Google Cloud Setup
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id-here
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account.json
GEMINI_MODEL=gemini-2.5-flash

# Database (Local by default)
DATABASE_ENGINE=sqlite

# Or for Cloud MySQL (optional):
# DATABASE_ENGINE=mysql
# MYSQL_HOST=your-database-host
# MYSQL_USER=your-username
# MYSQL_PASSWORD=your-password
# MYSQL_PORT=3306
# MYSQL_DATABASE=voltstream
```

⚠️ **IMPORTANT**: Never share your service account JSON file!

### **Step 5: Run Backend**

```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd backend
uvicorn main:app --reload
```

The backend will start at: `http://localhost:8000`

### **Step 6: Run Frontend (New PowerShell Window)**

```powershell
cd frontend
npm install
npm run dev
```

The frontend will start at: `http://localhost:5173`

### **Step 7: Open the App**

Go to: **http://localhost:5173** in your web browser

---

## � Deploy to Production

### **Deploy Frontend to Firebase** 🔥

```powershell
# 1. Install Firebase CLI
npm install -g firebase-tools

# 2. Login to Firebase
firebase login

# 3. Initialize Firebase in frontend folder
cd frontend
firebase init

# 4. Build the app for production
npm run build

# 5. Deploy to Firebase Hosting
firebase deploy --only hosting
```

**Your frontend will be live at:** `https://voltstream-project-95144.web.app`

### **Deploy Backend to Google Cloud Run** ☁️

```powershell
# 1. Install Google Cloud CLI
# Download from: https://cloud.google.com/sdk/docs/install

# 2. Authenticate with Google Cloud
gcloud auth login
gcloud config set project voltstreamapp

# 3. Build container image
cd backend
gcloud builds submit --tag gcr.io/voltstreamapp/voltstream-backend

# 4. Deploy to Cloud Run
gcloud run deploy voltstream-backend `
  --image gcr.io/voltstreamapp/voltstream-backend `
  --platform managed `
  --region us-central1 `
  --memory 512Mi `
  --set-env-vars GOOGLE_CLOUD_PROJECT=voltstreamapp

# 5. Get the service URL
gcloud run services describe voltstream-backend --region us-central1
```

**Your backend will be live at:** `https://voltstream-backend-*.run.app`

### **Connect Cloud SQL Database** 💾

```powershell
# 1. Create Cloud SQL instance (MySQL)
gcloud sql instances create voltstream-db `
  --database-version=MYSQL_8_0 `
  --tier=db-f1-micro `
  --region=us-central1 `
  --root-password=YourSecurePassword

# 2. Create database & user
gcloud sql databases create voltstream --instance=voltstream-db

# 3. Update .env with connection info
# Get IP address:
gcloud sql instances describe voltstream-db --format="value(ipAddresses[0].ipAddress)"
```

### **Update .env for Production**

```env
# Use Vertex AI
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=voltstreamapp
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash

# Use Cloud SQL instead of SQLite
DATABASE_ENGINE=mysql
MYSQL_HOST=35.202.131.68
MYSQL_USER=voltstream_user
MYSQL_PASSWORD=your-secure-password
MYSQL_PORT=3306
MYSQL_DATABASE=voltstream

# Update frontend to call deployed backend
VITE_API_URL=https://voltstream-backend-*.run.app
```

---

## �📡 API Endpoints (Complete Reference)

### **🏠 Dashboard & Data Endpoints**

| Method | Endpoint | Purpose | Returns |
|--------|----------|---------|---------|
| `GET` | `/api/v1/dashboard/live` | Current electricity usage | Live kW, solar, grid |
| `GET` | `/api/v1/analytics/history?period=daily` | Usage history | Daily usage data |
| `GET` | `/api/v1/analytics/history?period=weekly` | Weekly trends | 7-day data |
| `GET` | `/api/v1/analytics/history?period=monthly` | Monthly trends | 30-day data |
| `GET` | `/api/v1/billing/summary` | Bill info & budget | Total cost, balance |
| `PATCH` | `/api/v1/billing/summary` | Update budget limit | New budget |
| `GET` | `/api/v1/billing/trend` | Billing over time | Bill trend chart |

### **🏠 Device Control Endpoints**

| Method | Endpoint | Purpose | Input |
|--------|----------|---------|-------|
| `GET` | `/api/v1/devices` | List all devices | None |
| `POST` | `/api/v1/devices` | Add new device | Name, room, power |
| `PATCH` | `/api/v1/devices/{id}` | Toggle device on/off | Device ID |

### **🤖 AI Chat Endpoints**

| Method | Endpoint | Purpose | Input |
|--------|----------|---------|-------|
| `POST` | `/api/v1/chat` | Chat with AI | Message text |
| `POST` | `/api/v1/qa` | Ask energy question | Question text |
| `POST` | `/api/v1/agent` | Multi-agent routing | Message & type |
| `GET` | `/api/v1/qa/document` | Check document status | None |

### **💾 Document Upload**

| Method | Endpoint | Purpose | Input |
|--------|----------|---------|-------|
| `POST` | `/api/v1/documents/upload` | Upload PDF/text | File |
| `GET` | `/api/v1/documents/status` | Check indexed docs | None |

### **⚙️ System Endpoints**

| Method | Endpoint | Purpose | Returns |
|--------|----------|---------|---------|
| `GET` | `/health` | Server health check | Status: ok/error |
| `GET` | `/` | Root info | App name & docs |

---

## 🤖 AI Quality Testing

VoltStream includes **10 automatic tests** to verify AI answers are correct and helpful.

### **Test Questions**

| # | Question | Category |
|---|----------|----------|
| 1 | What is energy efficiency and why is it important for reducing costs and emissions? | Definitions |
| 2 | What are the recommended solar panel tilt angle and placement for maximum output? | Solar |
| 3 | What are the fastest low-cost actions to reduce home energy use? | Savings |
| 4 | Which appliances are good candidates for load shifting to solar production hours? | Optimization |
| 5 | Why should panels be kept clear of shade between 9 a.m. and 3 p.m.? | Solar |
| 6 | What does a high grid draw during bright midday hours typically indicate? | Monitoring |
| 7 | What are modern technologies used to improve energy efficiency? | Technology |
| 8 | What does a sudden increase in night usage often point to? | Analysis |
| 9 | What are the main challenges limiting energy efficiency improvements? | Challenges |
| 10 | How do smart grids and energy management systems contribute to efficiency? | Technology |

### **How to Test AI Quality**

Run the evaluation from command line:

```powershell
cd backend
python run_evaluation.py
```

### **Success Criteria**

✅ **PASS** = At least 7 out of 10 questions answered correctly  
❌ **FAIL** = Less than 7 questions answered correctly

Each answer is scored on:
- **Faithfulness** (1-5): Is it grounded in documents?
- **Relevance** (1-5): Does it answer the question?

The AI passes if it answers at least **7 out of 10 questions correctly**.

---

## 💾 Database Explained

### **Local Storage (Your Computer)**
- Stored in: `backend/databases/voltstream.sqlite3`
- Saves: Dashboard data, devices, billing info
- Use this for testing

### **Cloud Storage (Online)**
- Uses: Google Cloud MySQL
- Use this when deployed on internet

### **AI Search Storage**
- Stored in: `backend/databases/chroma_store/`
- Saves: Energy document information
- Used by AI to answer questions accurately

---

## 🔗 Important Links

| Link | Purpose |
|------|---------|
| [Frontend Website](https://voltstream-project-95144.web.app) | Live VoltStream (online version) |
| [Backend Server](https://voltstream-backend-335699237868.us-central1.run.app) | API (for advanced users) |
| [Google Cloud Console](https://console.cloud.google.com/) | Setup Google AI |
| [Python Downloads](https://www.python.org/downloads/) | Install Python |
| [Node.js Downloads](https://nodejs.org/) | Install Node.js |
| [Vertex AI Docs](https://cloud.google.com/vertex-ai/docs) | Learn about AI setup |

---

## ❓ Troubleshooting Guide

### **Installation Issues**

| Problem | Cause | Solution |
|---------|-------|----------|
| "Cannot find Python" | Python not installed | [Download Python 3.10+](https://www.python.org/downloads/) & check "Add to PATH" |
| "Module not found" | Packages not installed | Run: `pip install -r requirements.txt` |
| "Cannot find Node.js" | Node.js not installed | [Download Node.js LTS](https://nodejs.org/) |
| "npm not found" | npm not in PATH | Reinstall Node.js and check "Add to PATH" |

### **Configuration Issues**

| Problem | Error Message | Solution |
|---------|---------------|----------|
| Missing `.env` file | "GOOGLE_GENAI_USE_VERTEXAI not set" | Create `.env` file (copy from `.env.example`) |
| Wrong Google Cloud project | "INVALID_ARGUMENT" | Check `GOOGLE_CLOUD_PROJECT` matches GCP console |
| Bad credentials file | "PERMISSION_DENIED" | Verify `GOOGLE_APPLICATION_CREDENTIALS` path exists |
| Expired credentials | "Invalid or expired token" | Download new service account JSON from GCP |

### **Runtime Issues**

| Problem | Error Message | Solution |
|---------|---------------|----------|
| **Backend won't start** | Port 8000 in use | Change port: `uvicorn main:app --port 8001` |
| **Frontend won't connect** | Network error | Verify backend running at `http://localhost:8000` |
| **AI quota exceeded** | "429 RESOURCE_EXHAUSTED" | Wait 1 hour OR change model to `gemini-1.5-flash` |
| **Documents not loading** | "No context retrieved" | Verify files exist in `backend/data/` folder |
| **Database error** | "Can't connect to SQLite" | Delete `backend/databases/voltstream.sqlite3` and restart |

### **Deployment Issues**

| Problem | Platform | Solution |
|---------|----------|----------|
| **Frontend won't deploy** | Firebase | Run: `firebase deploy --only hosting` |
| **Backend won't deploy** | Cloud Run | Check `Dockerfile` exists in `backend/` folder |
| **Database connection fails** | Cloud SQL | Verify `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD` |
| **AI service unreachable** | Vertex AI | Check quota & enable Vertex AI API in GCP |

---

## 🎯 Command Quick Reference

### **Local Development**

| Command | What It Does | Location |
|---------|-------------|----------|
| `python -m venv venv` | Create Python environment | Root |
| `.\venv\Scripts\Activate.ps1` | Activate Python (Windows) | Root |
| `pip install -r requirements.txt` | Install Python packages | Root |
| `cd backend && uvicorn main:app --reload` | Start backend | Backend |
| `cd frontend && npm run dev` | Start frontend | Frontend |
| `cd backend && python run_evaluation.py` | Test AI answers | Backend |

### **Deployment**

| Command | What It Does | Platform |
|---------|-------------|----------|
| `gcloud builds submit` | Deploy backend | Google Cloud Run |
| `firebase deploy` | Deploy frontend | Firebase Hosting |
| `gcloud sql instances list` | Check database | Cloud SQL |
| `gcloud artifacts docker images` | View container images | Artifact Registry |

### **Windows Batch Scripts**

| Script | What It Does |
|--------|-------------|
| `start_backend.bat` | Start just the backend server |
| `start_voltstream.bat` | Start backend + frontend together |

---
  GEMINI_API_KEY=your-api-key-from-aistudio.google.com
  GEMINI_MODEL=gemini-2.0-flash-lite
  ```

### **Frontend won't connect to backend**
- Make sure backend is running on `http://localhost:8000`
- Check if port 8000 is already used:
  ```powershell
  netstat -ano | findstr :8000
  ```

### **Documents not loaded for AI Q&A**
- Check that these files exist:
  - `backend/data/energy_efficiency_guide.txt`
  - `backend/data/energy_efficiency_report.txt`
  - `backend/data/detailed_energy_efficiency_report.txt`

---

## 🎯 Quick Start Scripts (Windows)

### **Start Backend Only**
Double-click: `start_backend.bat`

### **Start Everything**
Double-click: `start_voltstream.bat`

---

## 📚 Learn More

### **For Developers**
- [React Documentation](https://react.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python Documentation](https://docs.python.org/3/)

### **For AI Concepts**
- [What is RAG (Retrieval Augmented Generation)?](https://cloud.google.com/vertex-ai/docs/generative-ai/rag-overview)
- [What is ChromaDB?](https://docs.trychroma.com/)
- [Vertex AI Gemini](https://cloud.google.com/vertex-ai/docs/generative-ai/learn/models)

---

## 🏭 Complete Deployment Architecture

### **What Runs Where**

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERNET USERS                            │
│                  (VoltStream Customers)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
┌─────────────────────┐            ┌──────────────────┐
│  🔥 FIREBASE        │            │  ☁️ GOOGLE CLOUD │
│  HOSTING            │            │  RUN             │
│                     │            │                  │
│  VoltStream         │            │  FastAPI         │
│  Website            │            │  Backend         │
│  (Frontend)         │            │  (API Server)    │
│                     │            │                  │
│ ✅ LIVE at:         │            │ ✅ LIVE at:      │
│ voltstream-...      │            │ voltstream-...   │
│ .web.app            │            │ .run.app         │
└──────────┬──────────┘            └─────────┬────────┘
           │                               │
           └───────────────┬───────────────┘
                           │
                ┌──────────┴──────────┬──────────┐
                │                    │          │
                ▼                    ▼          ▼
        ┌──────────────┐   ┌──────────────┐   ┌────────────┐
        │ ☁️ CLOUD SQL │   │ ☁️ VERTEX    │   │ ☁️ CLOUD   │
        │ MYSQL        │   │ AI GEMINI    │   │ STORAGE    │
        │              │   │              │   │            │
        │ Stores:      │   │ Powers:      │   │ Stores:    │
        │ - Usage data │   │ - Energy bot │   │ - Documents│
        │ - Devices    │   │ - Chatbot    │   │ - Embeddings
        │ - Billing    │   │ - Q&A        │   │ - ChromaDB │
        └──────────────┘   └──────────────┘   └────────────┘
```

### **Data Flow**

```
1. USER → Opens website in browser
2. Browser → Firebase loads React app
3. React app → Calls backend API
4. Backend → Processes request
5. Backend → Queries database (Cloud SQL)
6. Backend → Calls AI engine (Vertex AI)
7. AI → Searches documents (Cloud Storage)
8. Response → Sent back to frontend
9. Frontend → Shows result to user
```

### **Services by Platform**

| Service | Runs On | Cost | Purpose |
|---------|---------|------|---------|
| **Frontend (React)** | Firebase Hosting | Free (1GB/day) | Website UI |
| **Backend (FastAPI)** | Cloud Run | $0.40/M requests | API & logic |
| **Database (MySQL)** | Cloud SQL | $15/month | Data storage |
| **AI (Gemini)** | Vertex AI | $0.075/1K tokens | Smart answers |
| **Document Search** | Cloud Storage | $0.023/GB | File storage |

### **Local vs Production Comparison**

| Aspect | Local | Production |
|--------|-------|-----------|
| **Frontend** | `http://localhost:5173` | 🔥 Firebase Hosting |
| **Backend** | `http://localhost:8000` | ☁️ Cloud Run |
| **Database** | SQLite file | ☁️ Cloud SQL MySQL |
| **AI Engine** | Vertex AI (same) | Vertex AI (same) |
| **Speed** | Slow (your computer) | Fast (Google servers) |
| **Uptime** | Manual start/stop | 24/7 automatic |
| **Storage** | Limited to your disk | Unlimited cloud |

---

## 📄 Environment Variables Explained

| Variable | What It Does | Example |
|----------|-------------|---------|
| `GOOGLE_GENAI_USE_VERTEXAI` | Use Google Cloud AI? | `true` or `false` |
| `GOOGLE_CLOUD_PROJECT` | Your Google Cloud project name | `voltstreamapp` |
| `GOOGLE_CLOUD_LOCATION` | Where the AI runs | `us-central1` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to credentials file | `C:\path\to\file.json` |
| `GEMINI_MODEL` | Which AI model to use | `gemini-2.5-flash` |
| `DATABASE_ENGINE` | Where to save data | `sqlite` or `mysql` |
| `MYSQL_HOST` | Cloud database address | `35.202.131.68` |
| `MYSQL_USER` | Database username | `voltstream_user` |
| `MYSQL_PASSWORD` | Database password | `your-password` |

---

## 🔒 Security Tips

✅ **DO:**
- Keep `.env` file private (add to `.gitignore`)
- Don't share service account JSON files
- Use strong passwords for databases
- Regenerate keys if accidentally shared

❌ **DON'T:**
- Upload `.env` to GitHub
- Paste service account keys in Discord/Chat
- Share `GOOGLE_APPLICATION_CREDENTIALS` file
- Commit `voltstreamapp-*.json` files

---

## 🎉 You're Ready!

Your VoltStream app is now set up! Start with:

1. Open `http://localhost:5173` in your browser
2. Click **"Live Dashboard"** to see current usage
3. Click **"AI Assistant"** to chat with the energy bot
4. Click **"Smart Control"** to manage devices

Enjoy monitoring your energy! ⚡

---

## 📞 Need Help?

- Check the **Troubleshooting** section above
- Review `.env.example` for correct settings
- Make sure Python 3.10+  are installed
- Verify Google Cloud project has correct permissions
