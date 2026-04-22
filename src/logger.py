from logging.handlers import RotatingFileHandler
import logging
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_configured = False

class _NameFilter(logging.Filter):
    def __init__(self, prefix):
        self.prefix = prefix
        
    def filter(self, record):
        return record.name.startswith(self.prefix)

def _configure_root():
    global _configured
    if _configured:
        return
    
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setLevel(logging.INFO)
    stdout.setFormatter(formatter)
    
    debug = logging.FileHandler("logs/debug.log", mode='w')
    debug.setLevel(logging.DEBUG)
    debug.setFormatter(formatter)
    
    db = logging.FileHandler("logs/db.log", mode='w')
    db.setLevel(logging.DEBUG)
    db.addFilter(_NameFilter("src.data"))
    db.setFormatter(formatter)
    
    api = logging.FileHandler("logs/api.log", mode='w')
    api.setLevel(logging.DEBUG)
    api.addFilter(_NameFilter("src.api"))
    api.setFormatter(formatter)
    
    integrations = logging.FileHandler("logs/integrations.log", mode='w')
    integrations.setLevel(logging.DEBUG)
    integrations.addFilter(_NameFilter("src.integrations"))
    integrations.setFormatter(formatter)

    models = logging.FileHandler("logs/models.log", mode='w')
    models.setLevel(logging.DEBUG)
    models.addFilter(_NameFilter("src.models"))
    models.setFormatter(formatter)

    services = logging.FileHandler("logs/services.log", mode='w')
    services.setLevel(logging.DEBUG)
    services.addFilter(_NameFilter("src.services"))
    services.setFormatter(formatter)
    
    root.addHandler(stdout)
    root.addHandler(debug)
    root.addHandler(db)
    root.addHandler(api)
    root.addHandler(integrations)
    root.addHandler(models)
    root.addHandler(services)

    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("peewee").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    _configured = True

def get_logger(name: str) -> logging.Logger:
    _configure_root()
    return logging.getLogger(name)
