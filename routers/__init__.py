"""Top-level routers package re-exporting backend.app.routers."""
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.append(str(_BACKEND))

from app.routers import analytics, intake, integrations

__all__ = ["analytics", "intake", "integrations"]
