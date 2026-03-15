from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.api.routers import assets, factors, portfolio, screening
from fastapi.middleware.cors import CORSMiddleware
from src.logger import get_logger
import time
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logging.getLogger("uvicorn.access").disabled = True
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
        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.time() - start
            _logger.error(f"{request.method} {request.url.path} -> 500 ({duration:.3f}s) | {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        duration = time.time() - start
        _logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.3f}s)")
        return response
    
app.add_middleware(LoggingMiddleware)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    _logger.error(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.get("/test/error")
def test_error():
    raise ValueError("test error message")

@app.get("/test/crash")
def test_crash():
    raise Exception("something went wrong")

