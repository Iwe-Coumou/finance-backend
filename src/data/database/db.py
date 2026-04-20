from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_env_var
from src.logger import get_logger
from src.data.database.orm import Base
from contextlib import contextmanager

logger = get_logger(__name__)

_engine = None
_Session = None

def get_engine():
    global _engine
    if _engine is not None:
        return _engine
    try:
        _engine = create_engine(get_env_var("DB_URL"))
        logger.info("Connected to database")
        return _engine
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


@contextmanager
def get_session():
    global _Session
    if _Session is None:    
        _Session = sessionmaker(bind=get_engine())
    session = _Session()
    try:
        yield session
        session.commit()
        logger.debug("Session committed")
    except Exception as e:
        session.rollback()
        logger.warning(f"Session rolled back: {e}")
        raise
    finally:
        session.close()
        logger.debug("Session closed")

def create_tables():
    """Create all tables. Safe to run multiple times."""
    logger.info("Creating tables...")
    try:
        Base.metadata.create_all(get_engine())
        table_names = list(Base.metadata.tables.keys())
        logger.info(f"Tables created: {table_names}")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

if __name__ == "__main__":
    create_tables()
