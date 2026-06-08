from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.models.base import Base
# Import all models so Base knows about them before create_all
from app.models import user, ward, care_team, patient, device, alert, audit, insight, note, device_auth, ota, document, clinical_note, security, tenant, scheduling, workflow, developer

Base.metadata.create_all(bind=engine)

from app.core.audit_middleware import AuditMiddleware
from app.core.rate_limit_middleware import RateLimitMiddleware

app = FastAPI(title="Sentinel HealthOS", description="AI-powered remote patient monitoring and FHIR platform")

app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, patients, telemetry, monitoring, devices, alerts, wards, audit, documents, fhir, ai, copilot, care_team, ota, device_auth, telehealth, chronic_care, webrtc, transcription, ai_scribe, security, tenants, scheduling, tasks, workflows, reports, developer, exports

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(devices.router)
app.include_router(telemetry.router)
app.include_router(monitoring.router)
app.include_router(alerts.router)
app.include_router(fhir.router)
app.include_router(ai.router)
app.include_router(device_auth.router)
app.include_router(telehealth.router)
app.include_router(chronic_care.router)
app.include_router(wards.router)
app.include_router(care_team.router)
app.include_router(copilot.router)
app.include_router(documents.router)
app.include_router(audit.router)
app.include_router(ota.router)
app.include_router(webrtc.router)
app.include_router(transcription.router)
app.include_router(ai_scribe.router)
app.include_router(security.router)
app.include_router(tenants.router)
app.include_router(scheduling.router)
app.include_router(tasks.router)
app.include_router(workflows.router)
app.include_router(reports.router)
app.include_router(developer.router)
app.include_router(exports.router)

@app.get("/")
def read_root():
    return {"message": "Sentinel HealthOS API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
