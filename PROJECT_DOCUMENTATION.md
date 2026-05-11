# VoltStream Project Documentation

## 1. Project Overview

VoltStream is a full-stack smart energy monitoring web application. It is designed for users who consume electricity from the grid and also generate electricity using solar power.

The application helps users monitor:

- Live grid power usage
- Solar power generation
- Net power usage
- Smart device consumption
- Daily, weekly, and monthly usage analytics
- Billing projection and budget alerts

This version is a working prototype. The backend currently uses mock data, but the structure is ready for future integration with real smart meters, solar inverters, IoT devices, databases, and billing systems.

## 2. Technology Stack

### Frontend

- ReactJS: builds the user interface.
- Vite: runs and builds the React application.
- React Router: handles page routing.
- Tailwind CSS and custom CSS: styles the application.
- Recharts: displays energy data using charts.
- Lucide React: provides icons for navigation, buttons, cards, and alerts.
- Firebase Hosting: hosts the built frontend application.

### Backend

- FastAPI: creates REST API endpoints.
- Uvicorn: runs the FastAPI server.
- Pydantic: validates API request and response data.
- Docker: packages the backend into a container image.
- Google Cloud Run: hosts the backend API as a serverless container.

## 3. Application URLs

### Local URLs

Backend local URL:

```txt
http://127.0.0.1:8000/
```

Frontend local URL:

```txt
http://localhost:5175/
```

### Deployed URLs

Backend deployed on Google Cloud Run:

```txt
https://voltsream-api-335699237868.us-central1.run.app/
```

Frontend deployed on Firebase Hosting:

```txt
https://voltstream-project-95144.web.app/
```

## 4. High-Level Architecture

```txt
User Browser
    |
    v
Firebase Hosting
React Frontend
    |
    v
api.js fetch calls
    |
    v
Google Cloud Run
FastAPI Backend
    |
    v
Mock Data / Future Database or IoT Integration
```

The frontend is responsible for what the user sees and interacts with. The backend is responsible for providing structured data through API endpoints.

## 5. Project Flow

```txt
User opens frontend URL
    |
    v
index.html loads React app
    |
    v
main.jsx starts React Router
    |
    v
AppShell.jsx renders common layout and navigation
    |
    v
Selected page component loads
    |
    v
Page calls functions from api.js
    |
    v
api.js sends request to FastAPI backend
    |
    v
backend/api.py handles the route
    |
    v
mockdata.py provides sample data
    |
    v
data_models.py validates response format
    |
    v
Frontend receives response and displays UI
```

## 6. Main Use Cases

### Use Case 1: View Live Energy Dashboard

The user opens the dashboard and sees:

- Grid draw in kW
- Solar generation in kW
- Net usage
- Battery percentage
- Solar and grid trend charts

This helps the user understand current power status.

### Use Case 2: Analyze Energy Usage

The user opens the analytics page and compares:

- Grid energy usage
- Solar energy generation
- Net energy usage

The page supports daily, weekly, and monthly views.

### Use Case 3: Manage Smart Devices

The user opens the devices page and can:

- View all smart devices
- Filter by type, room, or status
- Add a new device
- Toggle a device ON or OFF
- See current active load

This helps users identify which appliances are consuming power.

### Use Case 4: Monitor Billing

The user opens the billing page and can:

- View current bill estimate
- View projected bill
- Set monthly budget limit
- See warning if projected bill exceeds the budget

This helps users control electricity cost.

### Use Case 5: Deploy Cloud Prototype

The backend is deployed to Google Cloud Run and the frontend is deployed to Firebase Hosting. This creates a public end-to-end demo that can be shown to officials, evaluators, or stakeholders.

## 7. File Structure

```txt
Voltstream_application/
    README.md
    PROJECT_DOCUMENTATION.md
    backend/
        Dockerfile
        .dockerignore
        requirements.txt
        main.py
        api.py
        data_models.py
        mockdata.py
        uvicorn.out.log
        uvicorn.err.log
    frontend/
        package.json
        package-lock.json
        index.html
        vite.config.js
        tailwind.config.js
        postcss.config.js
        firebase.json
        nginx.conf
        public/
            images/
                solar1.webp
                grid.jpg
                hybrid-solar-system.png
        src/
            main.jsx
            api.js
            hooks.js
            styles.css
            ui/
                AppShell.jsx
                State.jsx
            components/
                LiveDashboard.jsx
                UsageHistory.jsx
                SmartControl.jsx
                Invoices.jsx
                NotFound.jsx
```

## 8. Root Files

### README.md

Basic introduction to the project. It explains how to run the backend and frontend locally and lists the main features.

### PROJECT_DOCUMENTATION.md

Detailed documentation for future reference. It explains architecture, use cases, file purpose, local running, deployment, Docker, GCP, and Firebase.

## 9. Backend Files

### backend/Dockerfile

Defines how to containerize the FastAPI backend.

Important lines:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

Use:

- Creates a Python container.
- Installs backend dependencies.
- Copies backend code.
- Runs FastAPI using Uvicorn.
- Supports Cloud Run's dynamic `PORT` variable.

### backend/.dockerignore

Excludes unnecessary files from Docker build context.

Use:

- Avoids copying cache files.
- Avoids copying logs.
- Avoids copying virtual environments.
- Makes Docker image build cleaner and smaller.

### backend/requirements.txt

Contains backend Python dependencies:

```txt
fastapi
uvicorn[standard]
pydantic
```

Use:

- FastAPI builds APIs.
- Uvicorn runs the API server.
- Pydantic validates data models.

### backend/main.py

Creates the FastAPI application.

Use:

- Defines app title and version.
- Configures CORS.
- Allows frontend URLs to access backend APIs.
- Includes all routes from `api.py`.

### backend/api.py

Contains all API endpoints.

Main endpoints:

```txt
GET  /
GET  /health
GET  /api/v1/dashboard/live
GET  /api/v1/analytics/history
GET  /api/v1/devices
POST /api/v1/devices
PATCH /api/v1/devices/{device_id}
GET  /api/v1/billing/summary
```

Use:

- Serves dashboard data.
- Serves analytics data.
- Serves and updates device data.
- Serves billing summary.
- Provides health check endpoint.

### backend/data_models.py

Defines Pydantic models.

Use:

- Ensures API responses follow a fixed structure.
- Makes backend data safer and easier to understand.
- Helps auto-generate API documentation in FastAPI `/docs`.

Main models:

- `LivePowerSample`
- `LivePowerStatus`
- `EnergyDataPoint`
- `DeviceResponse`
- `DeviceCreate`
- `DeviceToggleResponse`

### backend/mockdata.py

Stores mock data used by the API.

Use:

- Acts like a temporary database.
- Provides live dashboard values.
- Provides usage history.
- Provides initial smart devices.
- Provides billing summary.

Future improvement:

- Replace this file with a real database or IoT data source.

### backend/uvicorn.out.log and backend/uvicorn.err.log

Runtime log files created while running the backend.

Use:

- `uvicorn.out.log` stores normal server output.
- `uvicorn.err.log` stores server errors.

These are not core source-code files.

## 10. Frontend Configuration Files

### frontend/package.json

Defines frontend dependencies and commands.

Important scripts:

```json
"dev": "vite --host 0.0.0.0",
"build": "vite build",
"preview": "vite preview --host 0.0.0.0"
```

Use:

- `npm run dev` starts local frontend.
- `npm run build` creates production files in `dist`.
- `npm run preview` previews the production build locally.

### frontend/package-lock.json

Locks exact npm dependency versions.

Use:

- Ensures the same dependency versions are installed on other machines.
- Improves deployment reliability.

### frontend/index.html

Base HTML file for the React app.

Important line:

```html
<div id="root"></div>
```

Use:

- React mounts the application inside this `root` element.

### frontend/vite.config.js

Configures Vite development server.

Use:

- Runs frontend on port `5175`.
- Proxies `/api` and `/health` requests to local backend.

This allows local frontend to call:

```txt
/api/v1/dashboard/live
```

while Vite forwards it to:

```txt
http://127.0.0.1:8000/api/v1/dashboard/live
```

### frontend/tailwind.config.js

Configures Tailwind CSS.

Use:

- Tells Tailwind which frontend files to scan for class names.

### frontend/postcss.config.js

Configures CSS processing.

Use:

- Enables Tailwind CSS.
- Enables Autoprefixer for browser compatibility.

### frontend/firebase.json

Firebase Hosting configuration.

Important parts:

```json
"public": "dist"
```

This means Firebase deploys the built frontend from the `dist` folder.

```json
"rewrites": [
  {
    "source": "**",
    "destination": "/index.html"
  }
]
```

This supports React Router routes like `/analytics`, `/devices`, and `/billing`.

### frontend/nginx.conf

Nginx configuration for serving the frontend in a container.

Use:

- Serves static frontend files.
- Proxies `/api` requests to backend.
- Supports frontend routing using `try_files`.

This file is useful if the frontend is deployed using Docker/Nginx instead of Firebase Hosting.

## 11. Frontend Source Files

### frontend/src/main.jsx

Main React entry point.

Use:

- Starts React.
- Configures browser routing.
- Maps URLs to page components.

Routes:

```txt
/           -> LiveDashboard.jsx
/analytics  -> UsageHistory.jsx
/devices    -> SmartControl.jsx
/billing    -> Invoices.jsx
/dashboard  -> redirects to /
*           -> NotFound.jsx
```

### frontend/src/api.js

Central file for frontend API calls.

Use:

- Defines backend base URL.
- Sends HTTP requests.
- Provides reusable functions for components.

Important variable:

```js
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
```

For production build, the backend URL must be passed as:

```cmd
set VITE_API_BASE_URL=https://voltsream-api-335699237868.us-central1.run.app
```

Main functions:

- `getLiveStatus()`
- `getUsageHistory(period)`
- `getDevices()`
- `addDevice(device)`
- `toggleDevice(deviceId)`
- `getBillingSummary()`

### frontend/src/hooks.js

Contains reusable React hook `useAsync`.

Use:

- Loads API data.
- Tracks loading state.
- Tracks error state.
- Stores returned data.

This avoids writing the same loading/error logic in every page.

### frontend/src/styles.css

Main stylesheet.

Use:

- Defines the full visual design.
- Styles layout, cards, dashboard, charts, device page, billing page, navigation, and responsive mobile views.

## 12. Frontend UI Files

### frontend/src/ui/AppShell.jsx

Main application layout.

Use:

- Displays brand logo and name.
- Displays sidebar navigation.
- Displays top navigation.
- Uses React Router `Outlet` to render the selected page.

### frontend/src/ui/State.jsx

Reusable loading and error UI.

Use:

- `LoadingState` shows loading message.
- `ErrorState` shows error message.

This improves user experience when API calls are in progress or fail.

## 13. Frontend Component Files

### frontend/src/components/LiveDashboard.jsx

Dashboard page.

Use:

- Shows real-time grid and solar power.
- Shows net usage.
- Shows savings.
- Displays solar and grid charts using Recharts.

API used:

```txt
GET /api/v1/dashboard/live
```

### frontend/src/components/UsageHistory.jsx

Analytics page.

Use:

- Shows energy usage history.
- Supports daily, weekly, and monthly views.
- Compares grid energy and solar generation.
- Shows total grid usage, solar generation, and net usage.

API used:

```txt
GET /api/v1/analytics/history?period=daily
GET /api/v1/analytics/history?period=weekly
GET /api/v1/analytics/history?period=monthly
```

### frontend/src/components/SmartControl.jsx

Devices page.

Use:

- Shows connected smart devices.
- Allows adding new devices.
- Allows toggling devices ON/OFF.
- Filters devices by type, status, and room.
- Shows active load.
- Displays selected device details.

APIs used:

```txt
GET   /api/v1/devices
POST  /api/v1/devices
PATCH /api/v1/devices/{device_id}
```

### frontend/src/components/Invoices.jsx

Billing page.

Use:

- Shows current bill estimate.
- Shows projected bill.
- Allows custom monthly budget limit.
- Stores budget limit in browser `localStorage`.
- Shows warning if projected bill exceeds budget.

API used:

```txt
GET /api/v1/billing/summary
```

### frontend/src/components/NotFound.jsx

404 page.

Use:

- Displays a friendly message for invalid routes.
- Provides a button to return to the dashboard.

## 14. Public Image Files

### frontend/public/images/solar1.webp

Solar panel image used in the dashboard.

### frontend/public/images/grid.jpg

Electrical grid image used in the dashboard.

### frontend/public/images/hybrid-solar-system.png

Solar system image asset available for future UI use.

## 15. Local Development Commands

### Run Backend Locally

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend opens at:

```txt
http://127.0.0.1:8000/
```

API documentation opens at:

```txt
http://127.0.0.1:8000/docs
```

### Run Frontend Locally

Open a second terminal:

```cmd
cd frontend
npm install
npm run dev
```

Frontend opens at:

```txt
http://localhost:5175/
```

## 16. Docker Commands For Backend

Run these commands from the project root or from the backend folder.

### Build Backend Docker Image

```cmd
cd backend
docker build -t voltstream-api .
```

Use:

- Reads `backend/Dockerfile`.
- Creates a Docker image named `voltstream-api`.
- Packages the backend with Python, dependencies, and source code.

### Run Backend Docker Container

```cmd
docker run --rm -p 8080:8080 voltstream-api
```

Use:

- Starts the backend container.
- Maps local port `8080` to container port `8080`.

Open:

```txt
http://127.0.0.1:8080/
```

### Run Backend Docker Container On Local Port 8000

```cmd
docker run --rm -p 8000:8080 voltstream-api
```

Use:

- Keeps the container running internally on `8080`.
- Makes it available locally at port `8000`.

Open:

```txt
http://127.0.0.1:8000/
```

### List Running Containers

```cmd
docker ps
```

Use:

- Shows active Docker containers.

### Stop A Running Container

```cmd
docker stop <container_id>
```

Use:

- Stops a running backend container.

## 17. Google Cloud Run Backend Deployment

### Purpose

Google Cloud Run is used to deploy the FastAPI backend as a serverless container.

Why Cloud Run is used:

- It runs containerized applications.
- It automatically scales based on traffic.
- It can scale down when not used.
- It provides a public HTTPS URL.
- It works well for APIs and backend services.

### Prerequisites

- Google Cloud account
- Billing enabled
- Google Cloud SDK installed
- GCP project selected
- Required APIs enabled

### Commands Used

```cmd
cd backend
gcloud auth login
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud run deploy voltstream-api --source .
```

Note: The correct service name is:

```txt
artifactregistry.googleapis.com
```

not:

```txt
artifactregistery.googleapis.com
```

### Explanation Of Each Command

```cmd
cd backend
```

Moves into the backend folder because the backend source code and Dockerfile are located there.

```cmd
gcloud auth login
```

Logs in to Google Cloud from the command line.

Use:

- Authenticates your Google account.
- Allows the CLI to deploy resources to your GCP project.

```cmd
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

Enables required Google Cloud services.

Use:

- `run.googleapis.com`: enables Cloud Run.
- `cloudbuild.googleapis.com`: enables Cloud Build to build the backend.
- `artifactregistry.googleapis.com`: enables Artifact Registry to store container images.

```cmd
gcloud run deploy voltstream-api --source .
```

Deploys the backend to Cloud Run.

Use:

- `voltstream-api` is the Cloud Run service name.
- `--source .` means deploy the current backend folder.
- Cloud Build builds the container.
- Artifact Registry stores the container image.
- Cloud Run starts the backend and gives a public HTTPS URL.

Deployed backend URL:

```txt
https://voltsream-api-335699237868.us-central1.run.app/
```

## 18. Firebase Frontend Deployment

### Purpose

Firebase Hosting is used to host the React frontend.

Why Firebase Hosting is used:

- It is suitable for static React applications.
- It provides free HTTPS hosting.
- It uses a global CDN.
- It supports single-page applications through rewrites.
- It can deploy the frontend with one CLI command.

### Commands Used

```cmd
cd frontend
npm install
set PATH=%APPDATA%\npm;%PATH%
npm install -g firebase-tools
firebase login
set VITE_API_BASE_URL=https://voltsream-api-335699237868.us-central1.run.app
npm run build
firebase deploy --only hosting
```

### Explanation Of Each Command

```cmd
cd frontend
```

Moves into the frontend folder because `package.json`, `firebase.json`, and React source files are there.

```cmd
npm install
```

Installs frontend dependencies from `package.json`.

Use:

- Installs React, Vite, Recharts, Lucide React, Tailwind, and other packages.

```cmd
set PATH=%APPDATA%\npm;%PATH%
```

Adds the global npm command folder to the current CMD session PATH.

Use:

- Helps Windows find globally installed commands like `firebase`.

```cmd
npm install -g firebase-tools
```

Installs Firebase CLI globally.

Use:

- Provides the `firebase` command.
- Required for Firebase login and deployment.

```cmd
firebase login
```

Logs in to Firebase from the command line.

Use:

- Authenticates your Firebase account.
- Allows deployment to your Firebase project.

```cmd
set VITE_API_BASE_URL=https://voltsream-api-335699237868.us-central1.run.app
```

Sets the backend API URL for the production frontend build.

Use:

- `api.js` reads this value through `import.meta.env.VITE_API_BASE_URL`.
- The deployed frontend will call the Cloud Run backend instead of local backend.

Important:

The variable must start with `VITE_` because Vite only exposes client-side environment variables with the `VITE_` prefix.

```cmd
npm run build
```

Builds the React frontend for production.

Use:

- Creates optimized static files inside `frontend/dist`.
- Firebase Hosting deploys this `dist` folder.

```cmd
firebase deploy --only hosting
```

Deploys only Firebase Hosting.

Use:

- Uploads `dist` folder to Firebase Hosting.
- Applies routing rules from `firebase.json`.
- Publishes the frontend website.

Deployed frontend URL:

```txt
https://voltstream-project-95144.web.app/
```

Note: The correct Firebase deploy command is:

```cmd
firebase deploy --only hosting
```

not:

```cmd
firebase run deploy --only hosting
```

## 19. Why Google Cloud SDK Is Used

Google Cloud SDK provides the `gcloud` command.

Use:

- Login to Google Cloud.
- Select and configure projects.
- Enable GCP services.
- Deploy backend to Cloud Run.
- View deployed services and logs.

Without Google Cloud SDK, backend deployment from local CMD would not be possible using `gcloud` commands.

## 20. Why Firebase CLI Is Used

Firebase CLI provides the `firebase` command.

Use:

- Login to Firebase.
- Initialize Firebase projects.
- Deploy frontend to Firebase Hosting.
- Manage hosting releases.
- Deploy only selected Firebase services using flags like `--only hosting`.

Without Firebase CLI, frontend deployment from local CMD would not be possible using `firebase deploy`.

## 21. Why Docker Is Used

Docker is used to package the backend application with everything it needs to run.

Use:

- Same backend environment everywhere.
- Easier deployment to Cloud Run.
- Avoids dependency mismatch between local and cloud.
- Makes the backend portable.

In this project:

- The backend Docker image contains Python.
- It installs dependencies from `requirements.txt`.
- It runs FastAPI using Uvicorn.

## 22. Important API Endpoints

### Root

```txt
GET /
```

Shows basic API information.

### Health Check

```txt
GET /health
```

Confirms the backend is running.

### Live Dashboard

```txt
GET /api/v1/dashboard/live
```

Returns real-time dashboard data.

### Usage History

```txt
GET /api/v1/analytics/history?period=daily
GET /api/v1/analytics/history?period=weekly
GET /api/v1/analytics/history?period=monthly
```

Returns energy usage history.

### Devices

```txt
GET /api/v1/devices
POST /api/v1/devices
PATCH /api/v1/devices/{device_id}
```

Used to view, add, and toggle smart devices.

### Billing

```txt
GET /api/v1/billing/summary
```

Returns billing summary data.

## 23. How To Explain To Higher Officials

Use this explanation:

VoltStream is a smart energy monitoring platform developed as a full-stack cloud-ready application. It helps users monitor grid electricity usage, solar generation, connected devices, and billing projections from a single web interface.

The frontend is built using React and deployed on Firebase Hosting. Firebase Hosting provides a secure HTTPS URL and serves the application through a fast hosting platform.

The backend is built using FastAPI and deployed on Google Cloud Run. Cloud Run runs the backend as a containerized serverless service. This means the API can scale based on usage and does not require manual server management.

The frontend communicates with the backend through REST APIs. The backend currently uses mock data for demonstration, but the architecture is prepared for real integrations such as smart meters, solar inverters, IoT devices, databases, and billing systems.

The project demonstrates an end-to-end cloud deployment flow:

- Backend containerization using Docker
- Backend deployment to Google Cloud Run
- Frontend build using Vite
- Frontend deployment to Firebase Hosting
- Public access through live HTTPS URLs

## 24. Short Presentation Script

VoltStream is a smart energy monitoring web application. It provides users with a live dashboard for grid and solar power, analytics for energy usage, smart device control, and billing projection.

The application has two parts. The frontend is developed in React and hosted on Firebase Hosting. The backend is developed in FastAPI and deployed on Google Cloud Run. The frontend calls backend APIs to get dashboard data, usage history, device data, and billing information.

For deployment, the backend is containerized using Docker and deployed to Cloud Run using the `gcloud` CLI. The frontend is built using Vite and deployed to Firebase Hosting using the Firebase CLI.

Currently, the system uses mock data for demonstration, but it can be extended to connect with real smart meters, IoT devices, solar inverters, databases, and billing systems.

## 25. Future Enhancements

- Add real database such as Firestore, PostgreSQL, or Cloud SQL.
- Connect real smart meters and solar inverter APIs.
- Add user authentication.
- Add role-based access for admins and customers.
- Add real-time WebSocket updates.
- Add AI-based energy-saving recommendations.
- Add alerts for high usage.
- Add monthly reports.
- Add payment gateway or billing integration.
- Add CI/CD pipeline for automatic deployment.

## 26. Common Mistakes To Avoid

### Mistake 1: Wrong Artifact Registry Service Name

Wrong:

```cmd
artifactregistery.googleapis.com
```

Correct:

```cmd
artifactregistry.googleapis.com
```

### Mistake 2: Wrong Firebase Deploy Command

Wrong:

```cmd
firebase run deploy --only hosting
```

Correct:

```cmd
firebase deploy --only hosting
```

### Mistake 3: Wrong Vite Environment Variable

Wrong:

```cmd
set vite_base_url=<backend-url>
```

Correct:

```cmd
set VITE_API_BASE_URL=<backend-url>
```

Reason:

The frontend code reads:

```js
import.meta.env.VITE_API_BASE_URL
```

Vite only exposes environment variables that start with `VITE_`.

### Mistake 4: Building Frontend Before Setting Backend URL

Set the backend URL before running:

```cmd
npm run build
```

Because Vite injects environment variables during build time.

## 27. Final Summary

VoltStream is a complete prototype of a cloud-deployed smart energy monitoring system. It has a React frontend, FastAPI backend, Docker containerization, Cloud Run backend deployment, and Firebase frontend deployment.

It is useful for demonstrating how modern cloud applications are built, deployed, and connected end-to-end.

