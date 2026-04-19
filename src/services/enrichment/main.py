from src.services.enrichment import region, figi
from src.logger import get_logger

_logger = get_logger(__name__)

def enrich_all(force: bool = False) -> None:
    _logger.info("Starting enrichment pipeline...")
    region.enrich(force=force)
    figi.enrich(force=force)
    _logger.info("Enrichment pipeline complete.")
    
if __name__ == "__main__":
    enrich_all()