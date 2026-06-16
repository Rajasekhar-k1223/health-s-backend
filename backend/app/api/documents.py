import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import RoleEnum
from app.models.document import Document
from app.models.patient import Patient
from app.schemas.document import DocumentResponse, SearchResult
from app.services.document_ai import process_document_pipeline

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    patient_id: int = Form(...),
    document_type: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    """Uploads a PDF and queues it for the OCR & AI extraction pipeline."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient or patient.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Patient does not belong to your organization")
        
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    doc = Document(
        patient_id=patient_id,
        filename=file.filename,
        file_path=file_path,
        document_type=document_type,
        status="processing"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Queue the heavy AI pipeline
    background_tasks.add_task(process_document_pipeline, doc.id)
    
    from app.services.fhir_sync import sync_document_reference
    background_tasks.add_task(sync_document_reference, doc.id, patient_id, doc.document_type, doc.status, doc.filename)
    
    return doc

@router.get("/patient/{patient_id}", response_model=List[DocumentResponse])
def get_patient_documents(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    """Returns all processed documents for a given patient."""
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient or patient.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Patient does not belong to your organization")
            
    return db.query(Document).filter(Document.patient_id == patient_id).order_by(Document.uploaded_at.desc()).all()

@router.post("/search", response_model=List[SearchResult])
def search_documents(
    query: str = Form(...),
    patient_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    """Semantic RAG search over processed medical documents via Qdrant."""
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin and patient_id:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient or patient.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Patient does not belong to your organization")
    elif current_user.role != RoleEnum.super_admin and not patient_id:
        raise HTTPException(status_code=400, detail="Global search requires a patient_id to enforce tenant isolation")

    try:
        from sentence_transformers import SentenceTransformer
        from qdrant_client import QdrantClient
        from qdrant_client.http import models

        model = SentenceTransformer('all-MiniLM-L6-v2')
        vector = model.encode([query])[0].tolist()
        QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=QDRANT_URL)
        
        filter_cond = None
        if patient_id:
            filter_cond = models.Filter(
                must=[models.FieldCondition(key="patient_id", match=models.MatchValue(value=patient_id))]
            )
            
        hits = client.search(collection_name="medical_documents", query_vector=vector, query_filter=filter_cond, limit=5)
        
        return [
            {
                "document_id": int(hit.id) if str(hit.id).isdigit() else 0, # Depending on how ID was stored
                "filename": hit.payload.get("filename", "Unknown"),
                "chunk_text": hit.payload.get("chunk_text", ""),
                "score": hit.score
            }
            for hit in hits
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
class QuestionnaireSubmit(BaseModel):
    patient_id: int
    questionnaire_name: str
    answers: dict

@router.post("/questionnaire")
def submit_questionnaire(
    qr_in: QuestionnaireSubmit,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse, RoleEnum.patient]))
):
    from app.models.questionnaire_response import QuestionnaireResponse
    
    # Enforce Multi-Tenant Data Governance
    if current_user.role != RoleEnum.super_admin:
        patient = db.query(Patient).filter(Patient.id == qr_in.patient_id).first()
        if not patient or patient.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Patient does not belong to your organization")
            
    qr = QuestionnaireResponse(
        patient_id=qr_in.patient_id,
        questionnaire_name=qr_in.questionnaire_name,
        answers=qr_in.answers,
        status="completed"
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    
    from app.services.fhir_sync import sync_questionnaire_response
    background_tasks.add_task(sync_questionnaire_response, qr.id, qr.patient_id, qr.questionnaire_name, qr.status, qr.answers)
    
    return {"id": qr.id, "status": "submitted"}
