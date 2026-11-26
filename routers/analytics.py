"""Analytics router proxy."""
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.append(str(_BACKEND))

from app.routers.analytics import *
from app.routers.analytics import router
