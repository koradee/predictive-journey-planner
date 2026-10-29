import os
from pathlib import Path
import sys

# Ensure repository root and relevant directories are in sys.path
CURRENT_FILE = Path(__file__).resolve()
ROOT_DIR = CURRENT_FILE.parent.parent

for p in [str(ROOT_DIR), str(ROOT_DIR / "backend"), str(ROOT_DIR / "routing")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.main import app
