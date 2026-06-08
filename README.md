# Sentinel HealthOS

AI-powered remote patient monitoring and FHIR healthcare platform MVP.

## Architecture

- **Frontend**: Next.js, TailwindCSS
- **Backend**: FastAPI
- **AI Service**: Python
- **Databases**: MySQL, MongoDB, Redis
- **FHIR**: HAPI FHIR R4

## Features

- Real-time telemetry streaming via WebSocket.
- AI/Rule-based anomaly detection (Tachycardia, Bradycardia, Low Oxygen, Fever, Respiratory Stress, Fall Detection).
- Patient, Device, and Alert CRUD.
- "Clinical insights for review" - No real medical diagnosis.

## Setup Steps (Sprint 1 & 2)

### 1. Start Infrastructure
Run the docker-compose to start MySQL, MongoDB, Redis, and HAPI FHIR.
```bash
docker-compose up -d
```

### 2. Configure Environment
Copy `.env` to the respective backend and frontend directories or keep it in the root if you use an env loader.
(A base `.env` is provided in the root directory).

### 3. Run Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*(Note: You will need to run Alembic or `Base.metadata.create_all(engine)` to init the MySQL DB schema. MVP testing can be done via FastAPI interactive docs at http://localhost:8000/docs)*

### 4. Run AI Engine & Simulator
```bash
cd ai-service
pip install -r requirements.txt
python app/engine.py
```

In another terminal:
```bash
cd device-simulator
python simulator.py
```
*The simulator sends synthetic vitals to the backend every 3 seconds.*

### 5. Run Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
*Open http://localhost:3000 to see the dashboard.*

## Testing Steps

1. Login or create a mock user via `/auth/register` (use the `/docs` page).
2. Create a mock patient and device via the API. Assign the device to the patient.
3. Start the simulator. Ensure telemetry is logged in the backend and AI Engine console.
4. Verify MongoDB has telemetry logs.
5. Trigger an alert by modifying `simulator.py` to send `heart_rate > 120`. Check the `/alerts` API endpoint to see the newly generated alert.
6. **FHIR Sync Testing**:
   - Use the `/fhir/sync/patient/{id}` and `/fhir/sync/device/{id}` APIs to sync records to the HAPI FHIR server.
   - You can view the synced FHIR records by visiting `http://localhost:8080/fhir/Patient` or `http://localhost:8080/fhir/Device` in your browser.
7. **AI & Doctor Workflow Testing**:
   - Check the `/ai/patient-insights/{patient_id}` endpoint to view the AI insights generated from the anomaly events.
   - Use `/ai/notes` to add a doctor note and update the patient's priority to `high` using `/ai/patient-priority/{patient_id}`.
   - Retrieve the comprehensive patient risk summary from `/ai/patient-summary/{patient_id}`.
8. Verify live streaming on the frontend Patient Details page (Requires Frontend UI integration).

## Disclaimer
This is a software demonstration only. **This is not a diagnosis. Clinical review is recommended.**
