from src.config import get_env_var
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != get_env_var("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")