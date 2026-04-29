from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from src.api.routers import assets, factors, portfolio, screening, holdings
from src.api.dependencies import verify_api_key
from fastapi.middleware.cors import CORSMiddleware
from src.logging.logger import get_logger
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

app.include_router(assets.router, prefix="/v1/assets", tags=["assets"], dependencies=[Depends(verify_api_key)])
app.include_router(factors.router, prefix="/v1/factors", tags=["factors"], dependencies=[Depends(verify_api_key)])
app.include_router(portfolio.router, prefix="/v1/portfolios", tags=["portfolios"], dependencies=[Depends(verify_api_key)])
app.include_router(screening.router, prefix="/v1/screening", tags=["screening"], dependencies=[Depends(verify_api_key)])
app.include_router(holdings.router, prefix="/v1/holdings", tags=["holdings"], dependencies=[Depends(verify_api_key)])
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.perf_counter() - start
            _logger.error(f"{request.method} {request.url.path} -> 500 ({duration:.3f}s) | {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        duration = time.perf_counter() - start
        path = request.url.path + (f"?{request.url.query}" if request.url.query else "")
        status_label = {200: "OK", 201: "Created", 400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found", 422: "Unprocessable", 500: "Server Error"}.get(response.status_code, "")
        label = f" ({status_label})" if status_label else ""
        _logger.info(f"{request.method} {path} -> {response.status_code}{label} ({duration:.3f}s)")
        return response
    
app.add_middleware(LoggingMiddleware)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    _logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    _logger.warning(f"ValueError on {request.url.path}: {exc}")
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

