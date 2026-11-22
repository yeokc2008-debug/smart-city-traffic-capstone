"""Compatibility launcher: execute the original CLI from the project root."""
from pathlib import Path
import logging
import runpy
import sys
logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
