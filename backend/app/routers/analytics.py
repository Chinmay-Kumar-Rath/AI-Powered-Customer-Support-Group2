"""Analytics and Reports router."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from .. import analytics, reports
from ..auth import staff_only
from ..database import get_db

router = APIRouter(tags=["analytics"])


@router.get("/analytics/overview")
def analytics_overview(user=Depends(staff_only), db: Session = Depends(get_db)):
    return analytics.overview(db)


@router.get("/analytics/trends")
def analytics_trends(
    days: int = Query(30, ge=1, le=365),
    format: Optional[str] = Query(None),
    user=Depends(staff_only),
    db: Session = Depends(get_db),
):
    if format in ("dict", "series"):
        return analytics.trends_dict(db, days)
    return analytics.trends(db, days)


@router.get("/analytics/categories")
def analytics_categories(
    format: Optional[str] = Query(None),
    user=Depends(staff_only),
    db: Session = Depends(get_db),
):
    if format == "dict":
        return analytics.categories_dict(db)
    return analytics.categories(db)


@router.get("/analytics/agent-performance")
def analytics_agents(
    format: Optional[str] = Query(None),
    user=Depends(staff_only),
    db: Session = Depends(get_db),
):
    if format == "dict":
        return analytics.agent_performance_dict(db)
    return analytics.agent_performance(db)


@router.get("/analytics/escalations")
def analytics_escalations(user=Depends(staff_only), db: Session = Depends(get_db)):
    return analytics.escalations(db)


@router.get("/analytics/satisfaction")
def analytics_satisfaction(user=Depends(staff_only), db: Session = Depends(get_db)):
    return analytics.satisfaction(db)


@router.get("/analytics/recurring-issues")
def analytics_recurring(
    format: Optional[str] = Query(None),
    user=Depends(staff_only),
    db: Session = Depends(get_db),
):
    if format == "dict":
        return analytics.recurring_issues_dict(db)
    return analytics.recurring_issues(db)


@router.get("/reports/summary")
def report_summary(
    format: Literal["csv", "pdf"] = "csv",
    user=Depends(staff_only),
    db: Session = Depends(get_db),
):
    report = analytics.summary(db)
    if format == "pdf":
        return Response(
            reports.to_pdf(report),
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="supportpilot-summary.pdf"'},
        )
    return Response(
        reports.to_csv(report),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="supportpilot-summary.csv"'},
    )
