"""Backwards-compatibility proxy for Role C routers."""
from fastapi import APIRouter
from integrations import imap_poller

from .routers.analytics import router as analytics_router
from .routers.intake import router as intake_router
from .routers.integrations import router as integrations_router

router = APIRouter()
router.include_router(intake_router)
router.include_router(integrations_router)
router.include_router(analytics_router)


def start_background_jobs():
    """Start the IMAP poller when configured."""
    return imap_poller.start_poller()
