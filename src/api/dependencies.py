# dependencies.py
from sqlalchemy.orm import Session
from src.data.database.db import get_engine
import redis
from src.config import get_env_var
from fastapi import security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = security(api_key_header)):
    if api_key != get_env_var("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")

def get_db():
    engine = get_engine()
    with Session(engine) as session:
        yield session

def get_redis():
    return redis.from_url(get_env_var("REDIS_URL"))