from app import agent_bridge

from .helpers import TICKET
from app.models import AgentRun


def test_diagnosis_and_validation_outputs_are_persisted(api, monkeypatch):
    diagnosis = {
        "summary": "VPN connectivity problem",
        "suspected_cause": "stale VPN session",
        "missing_information": [],
        "urgency": "medium",
        "confidence": 0.84,
    }
    validation = {"passed": True, "confidence": 0.81, "notes": "Grounded"}

    def run(db, ticket):
        return {
            "agent_trace": [
                {"agent": "Diagnosis", "status": "ok", "ms": 3, "confidence": 0.84,
                 "summary": diagnosis["summary"], "output": diagnosis},
                {"agent": "Validation", "status": "ok", "ms": 2, "confidence": 0.81,
                 "summary": validation["notes"], "output": validation},
            ],
            "diagnosis": diagnosis,
            "validation": validation,
            "resolution": {
                "response_text": "Try these steps.", "steps": ["a"], "sources": [], "articles": [],
                "confidence": 0.81, "mode": "extractive", "needs_human_review": False,
                "trace": [], "response_ms": 5,
            },
            "decision": "auto_resolve", "escalate_to": None, "reason": "",
        }

    monkeypatch.setattr(agent_bridge, "run", run)
    ticket = api.post("/tickets", json=TICKET).json()
    runs = api.get(f"/tickets/{ticket['ticket_id']}/agent-runs").json()
    assert runs[0]["output"] == diagnosis
    assert runs[1]["output"] == validation


def test_agent_analytics_reports_validation_metrics(api, session_factory):
    ticket = api.post("/tickets", json=TICKET).json()

    with session_factory() as db:
        db.query(AgentRun).delete()
        db.add_all([
            AgentRun(
                ticket_id=ticket["ticket_id"],
                agent_name="Validation",
                status="ok",
                confidence=0.8,
                output={"passed": True, "confidence": 0.8},
            ),
            AgentRun(
                ticket_id=ticket["ticket_id"],
                agent_name="Validation",
                status="failed",
                confidence=0.6,
                output={"passed": False, "confidence": 0.6},
            ),
        ])
        db.commit()

    response = api.get("/analytics/agents")
    assert response.status_code == 200

    validation = response.json()["validation"]
    assert validation["available"] is True
    assert validation["total_runs"] == 2
    assert validation["passed"] == 1
    assert validation["failed"] == 1
    assert validation["pass_rate"] == 50.0
    assert validation["average_confidence"] == 0.7


def test_agent_analytics_marks_validation_unavailable_when_empty(api):
    response = api.get("/analytics/agents")
    assert response.status_code == 200

    validation = response.json()["validation"]
    assert validation["available"] is False
    assert validation["total_runs"] == 0
    assert validation["passed"] == 0
    assert validation["failed"] == 0
    assert validation["pass_rate"] is None
    assert validation["average_confidence"] is None
    assert "No persisted validation outcomes" in validation["message"]

def test_normalize_adds_validation_trace_when_missing():
    result = agent_bridge._normalize({
        "agent_trace": [
            {"agent": "Diagnosis", "status": "ok"}
        ],
        "validation": {
            "passed": False,
            "confidence": 0.42,
            "notes": "Response needs review",
        },
        "resolution": {
            "response_text": "Please contact support.",
            "confidence": 0.42,
            "needs_human_review": True,
        },
    })

    validation_runs = [
        item for item in result["agent_trace"]
        if item.get("agent") == "Validation"
    ]

    assert len(validation_runs) == 1
    assert validation_runs[0]["status"] == "failed"
    assert validation_runs[0]["confidence"] == 0.42
    assert validation_runs[0]["output"]["passed"] is False
