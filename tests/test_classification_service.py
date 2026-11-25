
from unittest.mock import MagicMock, patch

from app import services
from app.models import Ticket
from app.schemas import TicketIn


def test_unknown_severity_is_saved_for_human_review():
    db = MagicMock()

    data = TicketIn(
        subject="Email attachment issue",
        description="I cannot open an email attachment.",
        email="employee@example.com",
        department="IT",
    )

    classification = {
        "category": "Email",
        "sub_category": "Attachments",
        "category_confidence": 0.85,
        "severity": "Unknown",
        "severity_confidence": 0.0,
        "priority": "P3",
        "needs_human_review": True,
    }

    def fake_flush():
        for obj in db.add.call_args_list:
            item = obj.args[0]
            if isinstance(item, Ticket):
                item.ticket_id = 123

    db.flush.side_effect = fake_flush

    with (
        patch.object(services, "get_or_create_user") as get_user,
        patch.object(services.classifier, "classify", return_value=classification),
        patch.object(services.hooks, "fire_notify"),
        patch("app.workflow.run_resolution_flow") as run_flow,
    ):
        get_user.return_value = MagicMock(user_id=10, email="employee@example.com")

        ticket = services.create_and_classify(db, data)

    assert ticket.category == "Email"
    assert ticket.severity == "Unknown"
    assert ticket.priority == "P3"
    assert ticket.status == "Classified"
    assert not any(
        "Classification failed" in str(call)
        for call in db.add.call_args_list
    )
    run_flow.assert_called_once_with(db, ticket)


def test_unknown_category_is_accepted_for_human_review():
    db = MagicMock()

    data = TicketIn(
        subject="Unclear issue",
        description="I am experiencing an unusual issue.",
        email="employee@example.com",
        department="IT",
    )

    classification = {
        "category": "Unknown",
        "sub_category": "Other",
        "category_confidence": 0.0,
        "severity": "Unknown",
        "severity_confidence": 0.0,
        "priority": "P3",
        "needs_human_review": True,
    }

    def fake_flush():
        for call in db.add.call_args_list:
            item = call.args[0]
            if isinstance(item, Ticket):
                item.ticket_id = 124

    db.flush.side_effect = fake_flush

    with (
        patch.object(services, "get_or_create_user") as get_user,
        patch.object(services.classifier, "classify", return_value=classification),
        patch.object(services.hooks, "fire_notify"),
        patch("app.workflow.run_resolution_flow") as run_flow,
    ):
        get_user.return_value = MagicMock(user_id=10, email="employee@example.com")

        ticket = services.create_and_classify(db, data)

    assert ticket.category == "Unknown"
    assert ticket.severity == "Unknown"
    assert ticket.status == "Classified"
    run_flow.assert_called_once_with(db, ticket)

from app import workflow


def test_unknown_severity_requires_human_escalation():
    ticket = Ticket(category="Email", severity="Unknown")

    result = {
        "resolution": {"needs_human_review": False, "confidence": 0.99},
        "decision": "auto_resolve",
    }

    reasons = workflow.decide(ticket, result)

    assert any("classification failed or returned Unknown" in reason for reason in reasons)


def test_unknown_category_requires_human_escalation():
    ticket = Ticket(category="Unknown", severity="Low")

    result = {
        "resolution": {"needs_human_review": False, "confidence": 0.99},
        "decision": "auto_resolve",
    }

    reasons = workflow.decide(ticket, result)

    assert any("classification failed or returned Unknown" in reason for reason in reasons)
