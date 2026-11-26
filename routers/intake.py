"""Intake router proxy."""
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.append(str(_BACKEND))

from app.routers.intake import *
from app.routers.intake import router
