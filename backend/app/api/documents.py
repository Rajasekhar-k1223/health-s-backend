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
    
    return doc

@router.get("/patient/{patient_id}", response_model=List[DocumentResponse])
def get_patient_documents(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor, RoleEnum.nurse]))
):
    """Returns all processed documents for a given patient."""
    return db.query(Document).filter(Document.patient_id == patient_id).order_by(Document.uploaded_at.desc()).all()

@router.post("/search", response_model=List[SearchResult])
def search_documents(
    query: str = Form(...),
    patient_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_role([RoleEnum.super_admin, RoleEnum.hospital_admin, RoleEnum.doctor]))
):
    """Semantic RAG search over processed medical documents via Qdrant."""
    try:
        # In a real setup:
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # vector = model.encode([query])[0].tolist()
        # client = QdrantClient(url=QDRANT_URL)
        # filter = models.Filter(...) if patient_id else None
        # hits = client.search(collection_name="medical_documents", query_vector=vector, query_filter=filter, limit=5)
        
        # Simulate results
        return [
            {
                "document_id": 1,
                "filename": "Lab_Results.pdf",
                "chunk_text": "Patient shows elevated glucose levels indicating potential hyperglycemia.",
                "score": 0.89
            }
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
