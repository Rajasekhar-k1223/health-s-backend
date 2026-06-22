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
from app.schemas.document import DocumentResponse, SearchResult, NewPatientUploadResponse
from app.services.document_ai import process_document_pipeline, extract_patient_from_text

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
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        # Only enforce org isolation when both sides have an org assigned
        if (patient.organization_id is not None and current_user.organization_id is not None
                and str(patient.organization_id) != str(current_user.organization_id)):
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

# ─────────────────────────────────────────────────────────────────────────────
# Auto-create patient from document
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/upload-new-patient", response_model=NewPatientUploadResponse)
async def upload_document_new_patient(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    """
    Uploads a PDF for an UNREGISTERED patient.
    - Runs synchronous OCR on the file
    - Calls Ollama LLM to extract patient demographics (name, DOB, gender, etc.)
    - Auto-creates a new Patient record
    - Links the document to the new patient
    - Queues the full AI pipeline (summarization, vectorization, FHIR sync)
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # 1 – Save the file
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2 – Synchronous OCR to get text for patient extraction
    extracted_text = ""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        images = convert_from_path(file_path)
        extracted_text = "\n".join(pytesseract.image_to_string(img) for img in images)
    except Exception as e:
        print(f"OCR warning (new-patient upload): {e}")
        extracted_text = f"PDF uploaded: {file.filename}"

    # 3 – LLM extraction of patient demographics
    info = await extract_patient_from_text(extracted_text)

    # 4 – Create Patient record
    import datetime as dt
    dob_val = None
    if info.get("dob"):
        try:
            dob_val = dt.date.fromisoformat(info["dob"])
        except Exception:
            dob_val = None

    age = int(info.get("age") or 0)
    if age == 0 and dob_val:
        today = dt.date.today()
        age = today.year - dob_val.year - ((today.month, today.day) < (dob_val.month, dob_val.day))

    new_patient = Patient(
        first_name=info.get("first_name", "Unknown"),
        last_name=info.get("last_name", "Patient"),
        dob=dob_val,
        age=max(age, 0),
        gender=info.get("gender"),
        contact_number=info.get("contact_number"),
        mrn=info.get("mrn"),
        organization_id=current_user.organization_id if hasattr(current_user, 'organization_id') else None,
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    # 5 – Create Document linked to the new patient
    doc = Document(
        patient_id=new_patient.id,
        filename=file.filename,
        file_path=file_path,
        document_type=document_type,
        status="processing",
        extracted_text=extracted_text,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6 – Queue background AI pipeline (summarization + vectorization + FHIR)
    background_tasks.add_task(process_document_pipeline, doc.id)

    patient_name = f"{new_patient.first_name} {new_patient.last_name}"
    return NewPatientUploadResponse(
        document_id=doc.id,
        patient_id=new_patient.id,
        patient_name=patient_name,
        extracted_info=info,
        status="processing",
        message=f"Patient '{patient_name}' auto-created (ID: {new_patient.id}). Document is now processing."
    )

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
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        # Only enforce org isolation when both sides have an org assigned
        if (patient.organization_id is not None and current_user.organization_id is not None
                and str(patient.organization_id) != str(current_user.organization_id)):
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
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        # Only enforce org isolation when both sides have an org assigned
        if (patient.organization_id is not None and current_user.organization_id is not None
                and str(patient.organization_id) != str(current_user.organization_id)):
            raise HTTPException(status_code=403, detail="Patient does not belong to your organization")

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
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        # Only enforce org isolation when both sides have an org assigned
        if (patient.organization_id is not None and current_user.organization_id is not None
                and str(patient.organization_id) != str(current_user.organization_id)):
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
