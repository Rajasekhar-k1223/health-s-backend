import json
import redis
import time
import requests
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models

REDIS_URL = os.getenv("AI_REDIS_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

r = redis.Redis.from_url(REDIS_URL)

# Try connecting to Qdrant, fail gracefully for MVP if not up yet
try:
    qdrant = QdrantClient(url=QDRANT_URL)
    qdrant.recreate_collection(
        collection_name="clinical_history",
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )
except Exception as e:
    print(f"Warning: Qdrant not available at {QDRANT_URL}. {e}")
    qdrant = None

def get_embedding(text):
    # In a real system, we'd use a fast local embedding model like all-MiniLM-L6-v2 via sentence-transformers.
    # For MVP, if Ollama has 'nomic-embed-text' or similar, we use it, otherwise we just generate a random/dummy vector to not block execution.
    try:
        res = requests.post(f"{OLLAMA_URL}/api/embeddings", json={
            "model": "llama3", # Assuming llama3 or fallback
            "prompt": text
        }, timeout=2)
        if res.status_code == 200:
            return res.json().get("embedding", [0.0]*384)[:384]
    except Exception:
        pass
    return [0.1] * 384

def ingest_to_qdrant(patient_id, text, metadata):
    if not qdrant: return
    vector = get_embedding(text)
    qdrant.upsert(
        collection_name="clinical_history",
        points=[
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"patient_id": patient_id, "text": text, **metadata}
            )
        ]
    )

def query_copilot(patient_id, prompt):
    context = ""
    if qdrant:
        try:
            vector = get_embedding(prompt)
            search_result = qdrant.search(
                collection_name="clinical_history",
                query_vector=vector,
                query_filter=models.Filter(
                    must=[models.FieldCondition(key="patient_id", match=models.MatchValue(value=patient_id))]
                ) if patient_id else None,
                limit=5
            )
            context = "\n".join([hit.payload.get("text", "") for hit in search_result])
        except Exception:
            pass

    system_prompt = f"""You are a Healthcare AI Copilot. Summarize the patient context and answer the doctor's query.
    Context: {context}
    
    IMPORTANT: You must always append the exact string at the end of your response: "This is not a diagnosis. Clinical review is recommended."
    """
    
    try:
        res = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "llama3",
            "prompt": prompt,
            "system": system_prompt,
            "stream": False
        }, timeout=30)
        return res.json().get("response", "Error generating response.")
    except Exception as e:
        return f"Failed to reach Local LLM (Ollama) at {OLLAMA_URL}. Ensure it is running. This is not a diagnosis. Clinical review is recommended."

def calculate_risk_score(vitals):
    score = 0
    hr = vitals.get("heart_rate", 80)
    spo2 = vitals.get("spo2", 98)
    temp = vitals.get("temperature", 37.0)
    resp = vitals.get("respiration_rate", 16)
    
    if hr > 100 or hr < 60: score += 20
    if hr > 120 or hr < 50: score += 30
    if spo2 < 95: score += 20
    if spo2 < 92: score += 30
    if temp > 37.5: score += 10
    if temp > 38.0: score += 20
    if resp > 20: score += 10
    if resp > 24: score += 20
    
    return min(score, 100)

def generate_insight(patient_id, category, score, summary):
    insight = {
        "patient_id": patient_id,
        "risk_category": category,
        "score": score,
        "summary": f"{summary} Based on available device signals only. This is not a diagnosis. Clinical review is recommended."
    }
    # Ingest insight to Qdrant for RAG
    ingest_to_qdrant(patient_id, summary, {"type": "insight", "category": category})
    
    try:
        requests.post(f"{BACKEND_URL}/ai/insights", json=insight)
    except Exception as e:
        pass

def detect_anomalies(patient_id, device_id, vitals):
    alerts = []
    
    hr = vitals.get("heart_rate")
    if hr and (hr > 120 or hr < 50):
        msg = "High severity tachycardia indicator." if hr > 120 else "Medium severity bradycardia indicator."
        alerts.append({"metric": "heart_rate", "value": hr, "severity": "high" if hr>120 else "medium", "message": msg})
        generate_insight(patient_id, "heart", 80 if hr>120 else 60, msg)
            
    spo2 = vitals.get("spo2")
    if spo2 and spo2 < 92:
        msg = "High severity low oxygen indicator."
        alerts.append({"metric": "spo2", "value": spo2, "severity": "high", "message": msg})
        generate_insight(patient_id, "respiratory", 90, msg)
        
    for alert in alerts:
        # Ingest to Qdrant
        ingest_to_qdrant(patient_id, alert["message"], {"type": "alert", "metric": alert["metric"]})
        
        alert["message"] += " This is not a diagnosis. Clinical review is recommended."
        alert["patient_id"] = patient_id
        alert["device_id"] = device_id
        
        try:
            requests.post(f"{BACKEND_URL}/alerts/", json=alert)
        except Exception:
            pass

def run_engine():
    print("AI Engine Started. Listening for telemetry...")
    while True:
        try:
            item = r.lpop("telemetry_stream")
            if item:
                data = json.loads(item)
                patient_id = data.get("patient_id")
                device_id = data.get("device_id")
                vitals = data.get("vitals", {})
                
                # Ingest raw vitals to vector db context
                vitals_text = f"Patient {patient_id} recorded HR: {vitals.get('heart_rate')}, SpO2: {vitals.get('spo2')}, Temp: {vitals.get('temperature')}"
                ingest_to_qdrant(patient_id, vitals_text, {"type": "telemetry"})
                
                risk_score = calculate_risk_score(vitals)
                detect_anomalies(patient_id, device_id, vitals)
                
            # Listen for copilot queries
            query_item = r.lpop("copilot_query_queue")
            if query_item:
                q_data = json.loads(query_item)
                response = query_copilot(q_data.get("patient_id"), q_data.get("prompt"))
                r.set(f"copilot_response:{q_data['query_id']}", response, ex=60)

        except Exception as e:
            print(f"Error in engine loop: {e}")
        time.sleep(1)

if __name__ == "__main__":
    run_engine()
