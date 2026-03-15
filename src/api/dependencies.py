# dependencies.py
from sqlalchemy.orm import Session
from src.data.database.db import get_engine
import redis
from src.config import get_env_var

def get_db():
    engine = get_engine()
    with Session(engine) as session:
        yield session

def get_redis():
    return redis.from_url(get_env_var("REDIS_URL"))