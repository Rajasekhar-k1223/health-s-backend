from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import SessionLocal
from app.models.audit import AuditLog

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Simple logging for MVP (Log all non-GET requests to patient/alert data)
        # Ideally, we decode the JWT token to get the user here
        path = request.url.path
        method = request.method
        
        if method in ["POST", "PUT", "PATCH", "DELETE"] and any(res in path for res in ["/patients", "/devices", "/alerts"]):
            db = SessionLocal()
            try:
                log = AuditLog(
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
