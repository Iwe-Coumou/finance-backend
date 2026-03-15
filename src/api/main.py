from fastapi import FastAPI

app = FastAPI(
    title="Finance Backend",
    description="Portfolio analytics and factor model API",
    version="0.1.0"
)

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

