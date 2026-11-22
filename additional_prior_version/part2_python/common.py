import logging
from pathlib import Path
def logger(): return logging.getLogger(__name__)
def configure(level=logging.INFO):
 root=logging.getLogger(); root.setLevel(level)
 if root.handlers: return
 fmt=logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
 for h in [logging.StreamHandler(),logging.FileHandler(Path(__file__).parent/'pipeline.log',mode='w')]: h.setFormatter(fmt); root.addHandler(h)
