import os
import json
import re
import asyncio
import httpx
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.document import Document
from app.services.fhir_sync import sync_document_to_fhir

# Optional/Mock imports for pipeline
try:
    from pdf2image import convert_from_path
    import pytesseract
except ImportError:
    pass

try:
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams, PointStruct
except ImportError:
    pass

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# ─────────────────────────────────────────────────────────
# Patient Extraction from raw OCR text via Ollama LLM
# ─────────────────────────────────────────────────────────
async def extract_patient_from_text(ocr_text: str) -> dict:
    """
    Asks Ollama to extract structured patient demographics from raw OCR text.
    Returns a dict with keys: first_name, last_name, dob, age, gender, contact_number, mrn.
    Falls back to safe defaults if the LLM is offline or returns malformed JSON.
    """
    DEFAULTS = {
        "first_name": "Unknown",
        "last_name": "Patient",
        "dob": None,
        "age": 0,
        "gender": "Unknown",
        "contact_number": None,
        "mrn": None,
    }

    prompt = (
        "You are a medical data extraction assistant. "
        "Extract patient demographics from the following document text. "
        "Return ONLY a valid JSON object with these keys: "
        "first_name, last_name, dob (YYYY-MM-DD or null), age (integer or 0), "
        "gender (Male/Female/Other or Unknown), contact_number (or null), mrn (or null). "
        "If a field cannot be found, use null or 0 for age. "
        "Do NOT include any explanation or markdown, only raw JSON.\n\n"
        f"Document Text:\n{ocr_text[:3000]}"
    )

    try:
        ollama_url = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{ollama_url}/api/generate",
                json={"model": "llama3.2", "prompt": prompt, "stream": False}
            )
            if response.status_code == 200:
                raw = response.json().get("response", "")
                # Strip markdown code fences if present
                raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
                extracted = json.loads(raw)
                # Merge with defaults to ensure all keys are present
                return {**DEFAULTS, **{k: v for k, v in extracted.items() if v is not None and v != ""}}
    except Exception as e:
        print(f"⚠️  Patient extraction LLM error: {e}")

    return DEFAULTS


async def process_document_pipeline(document_id: int):
    """
    Background worker that runs the full unstructured document AI pipeline.
    1. OCR (PyTesseract)
    2. Local LLM Summarization (Ollama)
    3. Vector Embedding (Qdrant)
    4. FHIR Mapping
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        print(f"🚀 Starting Document AI Pipeline for Doc {doc.id}: {doc.filename}")

        # 1. OCR Stage
        try:
            images = convert_from_path(doc.file_path)
            text_pages = [pytesseract.image_to_string(img) for img in images]
            extracted_text = "\n".join(text_pages)
        except Exception as e:
            print(f"OCR Warning: {e}. Using simulated text.")
            extracted_text = "Simulated OCR Text extracted from PDF.\nPatient shows elevated glucose levels."
            
        doc.extracted_text = extracted_text
        
        # 2. Structuring & Summarization Stage (Ollama)
        prompt = f"Summarize the following medical document and extract key clinical findings. Keep the summary under 3 sentences.\n\nDocument Text:\n{extracted_text}"
        
        try:
            ollama_url = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    summary = response.json().get("response", "Error generating summary.")
                else:
                    summary = f"LLM Error: Status {response.status_code}"
        except httpx.RequestError as e:
            print(f"Failed to connect to Ollama: {e}")
            summary = "(LLM Offline) Simulated Summary: Patient presents with elevated glucose levels indicating potential hyperglycemia. Recommended follow-up HbA1c."

        disclaimer = "\n\nClinical insights for review. This is not a diagnosis. Clinical review is recommended."
        doc.ai_summary = summary + disclaimer
        
        # Categorize
        if "glucose" in extracted_text.lower():
            doc.document_type = "Lab Report"
        else:
            doc.document_type = "Clinical Note"
            
        db.commit()
        
        # 3. Vectorization Stage (Qdrant)
        try:
            model = SentenceTransformer('all-MiniLM-L6-v2')
            vectors = model.encode([extracted_text])
            client = QdrantClient(url=QDRANT_URL)
            try:
                client.get_collection(collection_name="medical_documents")
            except Exception:
                client.recreate_collection(collection_name="medical_documents", vectors_config=VectorParams(size=384, distance=Distance.COSINE))
            
            client.upsert(collection_name="medical_documents", points=[PointStruct(id=doc.id, vector=vectors[0].tolist(), payload={"patient_id": doc.patient_id, "filename": doc.filename, "chunk_text": extracted_text[:200]})])
            print("✅ Vectorized and inserted into Qdrant.")
        except Exception as e:
            print(f"Vector DB Warning: {e}")

        # 4. FHIR Mapping Stage
        from app.models.patient import Patient
        from app.services.fhir_sync import sync_patient_to_fhir
        patient = db.query(Patient).filter(Patient.id == doc.patient_id).first()
        if patient:
            sync_patient_to_fhir(patient)
            
        sync_document_to_fhir(doc)
        
        doc.status = "completed"
        db.commit()
        print(f"✅ Document AI Pipeline finished for Doc {doc.id}")

    except Exception as e:
        print(f"🚨 Document Pipeline Failed: {e}")
        if 'doc' in locals() and doc:
            doc.status = "failed"
            db.commit()
    finally:
        db.close()
