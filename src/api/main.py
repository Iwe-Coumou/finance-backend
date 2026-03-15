from fastapi import FastAPI, Request
from src.api.routers import assets, factors, portfolio, screening
from fastapi.middleware.cors import CORSMiddleware
from src.logger import get_logger
import time
from starlette.middleware.base import BaseHTTPMiddleware

_logger = get_logger(__name__)

app = FastAPI(
    title="Finance Backend",
    description="Portfolio analytics and factor model API",
    version="0.1.0"
)

app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(factors.router, prefix="/factors", tags=["factors"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(screening.router, prefix="/screening", tags=["screening"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        _logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.3f}s)")
        return response
    
app.add_middleware(LoggingMiddleware)

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

