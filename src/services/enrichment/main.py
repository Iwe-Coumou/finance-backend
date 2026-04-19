from src.services.enrichment import region, figi, isin
from src.logger import get_logger

_logger = get_logger(__name__)

def enrich_all(force: bool = False) -> None:
    _logger.info("Starting enrichment pipeline...")
    
    # Order matters, the figi code depends on isin being available
    isin.enrich(force=force)
    figi.enrich(force=force)
    
    # Derived from existing data so fully self contained
    region.enrich(force=force)
    
    _logger.info("Enrichment pipeline complete.")
    
if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    enrich_all(force=force)