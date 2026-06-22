from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    patient_id: int
    filename: str
    document_type: Optional[str] = None

class DocumentCreate(DocumentBase):
    file_path: str

class DocumentResponse(DocumentBase):
    id: int
    status: str
    ai_summary: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

class SearchResult(BaseModel):
    document_id: int
    filename: str
    chunk_text: str
    score: float

class NewPatientUploadResponse(BaseModel):
    """Returned when a document is uploaded for an unregistered patient."""
    document_id: int
    patient_id: int
    patient_name: str
    extracted_info: Dict[str, Any]
    status: str
    message: str
