from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from app.core.database import SessionLocal
from app.models.audit import AuditLog
from app.core.security import SECRET_KEY, ALGORITHM

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # HIPAA Compliance: Log ALL requests to PHI data (including GET/views)
        path = request.url.path
        method = request.method
        
        # Define PHI endpoints that require auditing
        phi_endpoints = ["/patients", "/devices", "/alerts", "/telehealth", "/documents", "/clinical_notes"]
        
        if any(res in path for res in phi_endpoints):
            # Cryptographically extract identity
            username = "Unknown/Anonymous"
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                    username = payload.get("sub", "Unknown")
                except JWTError:
                    username = "InvalidToken"

            db = SessionLocal()
            try:
                log = AuditLog(
                    username=username,
                    action=method,
                    resource=path,
                    ip_address=request.client.host
                )
                db.add(log)
                db.commit()
            except Exception as e:
                print(f"Audit log error: {e}")
            finally:
                db.close()
                
        return response
