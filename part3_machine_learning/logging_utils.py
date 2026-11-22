"""Entry points call configure_logging; library modules only acquire named loggers."""
import logging
from pathlib import Path
logger = logging.getLogger(__name__)

def configure_logging(path, debug=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    # A shared parent routes named module loggers; no library function uses root calls.
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    for handler in (logging.StreamHandler(), logging.FileHandler(path, encoding='utf-8')):
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG if debug else logging.INFO)
        root.addHandler(handler)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
