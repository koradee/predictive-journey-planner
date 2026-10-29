# Demo Guide: Predictive Journey Planner (Frontend + Backend)

This guide explains how to install dependencies, run the FastAPI backend, run the React frontend, and verify the end-to-end Pune journey planning demonstration on Windows PowerShell.

---

## 1. Prerequisites

- **Python**: 3.10+ (tested on Python 3.14)
- **Node.js**: 20 LTS or 24 LTS (with npm)
- **Git**

---

## 2. Dependency Installation

Open Windows PowerShell in the project directory (`predictive-journey-planner`):

### A. Python Backend Dependencies
```powershell
python -m pip install -r backend/requirements.txt
```

This installs:
- `fastapi` (REST API framework)
- `uvicorn` (ASGI web server)
- `pydantic` (Request/response validation)
- `networkx` (Graph routing algorithms)
- `httpx` (HTTP client for test suite)

### B. React Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

---

## 3. Starting the Servers

Running the application requires two PowerShell terminals: one for the backend and one for the frontend.

### Terminal 1: Start FastAPI Backend
From the repository root:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Expected startup output:
```text
INFO:     Started server process
INFO:pjp-backend:Initializing Predictive Journey Planner backend...
INFO:pjp-backend:Pune OSM routing graph verified and ready (12325 nodes, 22104 edges).
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

You can verify the backend endpoints in a browser or PowerShell:
- **Liveness probe**: `http://127.0.0.1:8000/api/health`
- **Routing data readiness**: `http://127.0.0.1:8000/api/ready`

### Terminal 2: Start React Frontend
From the repository root:
```powershell
cd frontend
npm run dev
```

Expected startup output:
```text
  VITE v8.3.5  ready in 200 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## 4. Demonstrating the Journey

1. Open **`http://localhost:5173/`** in Google Chrome or any modern browser.
2. In the "Where would you like to go?" journey planner form:
   - **Starting location**: `Shivajinagar, Pune`
   - **Destination**: `Pune Railway Station`
   - **Travel date**: Choose a future date (e.g. tomorrow)
   - **Departure time**: Choose a time (e.g. `14:00`)
3. Click **Find Routes →**.
4. The application transitions to the Results view (`#results`):
   - A loading banner appears while the backend calculates routes.
   - The frontend sends `POST /api/routes` with journey parameters.
   - The backend validates the request, snaps coordinates to the Pune OSM road graph, and calculates actual paths.
   - The map loads OpenStreetMap tiles and renders the real road path (99 OSM coordinates) in blue with markers at the snapped start and destination points.
   - The Route Card displays the calculated distance (**3.35 km**) and selection state.
5. **Testing Error Handling & Backend Failure**:
   - Click **Edit Journey**.
   - Enter an unsupported location such as `Mumbai` and click **Find Routes**.
   - Notice that the app displays a clear error state (*"Location 'Mumbai' is unsupported or outside the bounded Pune pilot area"*), with a **Retry** button and **Edit Journey** button.
   - Fabricated or hardcoded demo routes are never shown when the backend reports an error.

---

## 5. How Frontend and Backend Communicate

1. **Proxy in Development**:
   - `frontend/vite.config.js` configures a reverse proxy: any frontend request to `/api/*` is forwarded to `http://127.0.0.1:8000/api/*`.
2. **CORS Support**:
   - `backend/main.py` configures `CORSMiddleware` so the API can also be called directly across origins if needed.
3. **Data Protocol**:
   - Request payload (`POST /api/routes`):
     ```json
     {
       "source": "Shivajinagar, Pune",
       "destination": "Pune Railway Station",
       "travelDate": "2026-10-30",
       "departureTime": "14:00",
       "alternatives": 3,
       "objective": "distance"
     }
     ```
   - Response payload:
     - GeoJSON `geometry` (standard `[lon, lat]` EPSG:4326).
     - Leaflet `coordinates` (`[lat, lon]`).
     - Real calculated `distance_km` (e.g. `3.355`).
     - Snapped node IDs, distances to snaps, and OSM way IDs.

---

## 6. What Functionality is Real vs. Future Work

### Real and Operational
- **Real Road Network**: Loaded directly from `data/raw/pune-osm/roads.json` (3.7 MB, 12,325 nodes, 22,104 directed edges) verified against SHA256 checksum in `data/pune-osm-manifest.json`.
- **Accurate Routing**: Directed NetworkX Dijkstra / shortest simple paths algorithm respecting one-way streets, car access tags, and boundary clipping.
- **True Road Geometry**: High-resolution line strings following real Pune streets (e.g. Jangali Maharaj Road, Sancheti Hospital flyover corridor, Station Road).
- **Distance Calculation**: Exact spherical great-circle distance along road network segments.
- **Interactive UI**: Real-time Leaflet map rendering with route selection, markers, loading spinners, and error alerts with retry.

### Future Work
- **Live AI Traffic Prediction**: The XGBoost models in `ml/` benchmark traffic on the Los Angeles (METR-LA) dataset as a research baseline. Integrating dynamic traffic predictions for Pune requires localized sensor or probe telemetry.
- **Turn Delays & Signals**: Junction delays and signal phases are not yet simulated in OSM graph edges.
- **User Accounts & Persistence**: Journeys currently reside in memory for presentation; database persistence (e.g., PostgreSQL) is planned for a later phase.

---

## 7. Running Automated Tests

### Backend Unit Tests
From repository root:
```powershell
python -m unittest backend/test_backend.py
```
*Expected: 9 tests run, 0 failures, 0 errors.*

### Frontend Tests, Linting, and Production Build
From repository root:
```powershell
cd frontend
npm test
npm run lint
npm run build
cd ..
```
*Expected: 14 tests pass, oxlint reports 0 warnings and 0 errors, Vite production build completes cleanly.*

