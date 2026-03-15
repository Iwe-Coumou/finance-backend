from fastapi import FastAPI
from src.api.routers import assets, factors, portfolio, screening

app = FastAPI(
    title="Finance Backend",
    description="Portfolio analytics and factor model API",
    version="0.1.0"
)

app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(factors.router, prefix="/factors", tags=["factors"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(screening.router, prefix="/screening", tags=["screening"])

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

