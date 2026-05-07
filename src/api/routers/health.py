from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.data.database.db import get_engine
from src.config import get_env_var
from src.logging.logger import get_logger
from sqlalchemy import text
import redis

router = APIRouter()

_logger = get_logger(__name__)


def _check_db() -> str | None:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return None
    except Exception as e:
        return str(e).splitlines()[0]


def _check_redis() -> str | None:
    try:
        client = redis.from_url(get_env_var("REDIS_URL"))
        client.ping()
        return None
    except Exception as e:
        return str(e).splitlines()[0]


_REQUIRED = {"database": _check_db}
_OPTIONAL = {"redis": _check_redis}


@router.get("/health")
def health():
    required = {name: fn() for name, fn in _REQUIRED.items()}
    optional = {name: fn() for name, fn in _OPTIONAL.items()}

    services = {
        name: "ok" if err is None else f"error: {err}"
        for name, err in {**required, **optional}.items()
    }

    required_ok = all(err is None for err in required.values())
    optional_ok = all(err is None for err in optional.values())

    if not required_ok:
        status, status_code = "error", 503
    elif not optional_ok:
        status, status_code = "degraded", 200
    else:
        status, status_code = "ok", 200

    if not required_ok or not optional_ok:
        failed = [name for name, err in {**required, **optional}.items() if err is not None]
        _logger.warning(f"Health check: {status} — {failed}")

    return JSONResponse(
        status_code=status_code,
        content={"status": status, "services": services},
    )
