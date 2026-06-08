from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from collections import defaultdict

# Naive in-memory rate limiter for MVP
# Max 100 requests per minute per IP
RATE_LIMIT = 100
TIME_WINDOW = 60

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_counts = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean up old requests
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if current_time - req_time < TIME_WINDOW
        ]
        
        if len(self.request_counts[client_ip]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )
            
        self.request_counts[client_ip].append(current_time)
        response = await call_next(request)
        return response
