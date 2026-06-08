import os
import json
import redis
import time
from faster_whisper import WhisperModel
import pymongo

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:rootpassword@mongodb:27017")
QUEUE_NAME = "transcription_jobs"

# Load the whisper model
# Using CPU by default as per requirements: "Support CPU first, GPU optional later"
print("Loading Whisper model...")
model_size = "tiny.en"  # "base" or "small" can be used depending on resources
model = WhisperModel(model_size, device="cpu", compute_type="int8")
print("Model loaded.")

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Connect to MongoDB
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client["sentinel"]
transcripts_coll = db["transcripts"]

def process_job(job_data_str):
    try:
        job_data = json.loads(job_data_str)
        visit_id = job_data["visit_id"]
        file_path = job_data["file_path"]
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
            
        print(f"Processing audio for visit {visit_id}: {file_path}")
        
        # Run transcription
        segments, info = model.transcribe(file_path, beam_size=5)
        
        text_segments = []
        for segment in segments:
            text_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            
        # Optional: Speaker diarization could be added here
        # For now, append to the document in MongoDB
        if text_segments:
            # We add a new timeline event or append to the visit's transcript
            # In a real scenario, we'd assign speaker dynamically
            transcript_entry = {
                "visit_id": visit_id,
                "timestamp": time.time(),
                "segments": text_segments,
                # Default mock speaker for now
                "speaker": "Unknown"
            }
            transcripts_coll.insert_one(transcript_entry)
            
            # Publish result to redis so backend can send via WebSockets
            r.publish(f"transcription_results:{visit_id}", json.dumps({
                "visit_id": visit_id,
                "segments": text_segments,
                "speaker": "Unknown"
            }))
            
        # Clean up temporary audio file
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error removing {file_path}: {e}")
            
    except Exception as e:
        print(f"Error processing job: {e}")

def main():
    print(f"Listening for jobs on queue: {QUEUE_NAME}")
    while True:
        try:
            # Block and wait for a job
            result = r.blpop(QUEUE_NAME, timeout=0)
            if result:
                queue, job_data = result
                process_job(job_data.decode('utf-8'))
        except Exception as e:
            print(f"Redis error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
