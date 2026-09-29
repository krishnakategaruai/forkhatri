"""[047] One moderation queue item per reported thing, and admin text written for people."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.api.routes.admin import _day, _summary
from app.components.safety.interface import Report, group_reports


def _report(reporter, subject, reason="misleading", status="open", minutes=0):
    t = datetime(2026, 9, 13, 18, 0, tzinfo=UTC) + timedelta(minutes=minutes)
    return Report(uuid4(), reporter, "occurrence", subject, reason, None, status, t, t)


def test_repeats_and_other_reporters_collapse_into_one_item():
    priya, vikram, subject, other = uuid4(), uuid4(), uuid4(), uuid4()
    reports = [_report(priya, subject, minutes=m) for m in range(7)] + [_report(vikram, subject, "unsafe", minutes=30), _report(priya, other)]
    groups = group_reports(reports)
    assert len(groups) == 2
    g = next(g for g in groups if g.lead.subject_id == subject)
    assert g.reporter_count == 2 and len(g.reports) == 8
    assert g.lead.created_at == min(r.created_at for r in g.reports)
    assert g.is_safety and g.lead_reason == "unsafe"
    # the unsafe report (+30 min) is due within 24 h, earlier than the misleading ones' 72 h
    assert g.due_at == reports[7].created_at + timedelta(hours=24)


def test_different_statuses_stay_separate_items():
    subject, who = uuid4(), uuid4()
    assert len(group_reports([_report(who, subject), _report(who, subject, status="dismissed")])) == 2


def test_summary_and_dates_are_for_people():
    assert _summary("misleading", "Evening badminton doubles", 1, "en") == "Reported as misleading: Evening badminton doubles"
    assert _summary("spam", "Trek", 3, "en").endswith("3 people reported this")
    assert _day(datetime(2026, 9, 13, 5, 0, tzinfo=UTC), "en") == "13 Sep 2026"
    assert _day(datetime(2026, 9, 13, 5, 0, tzinfo=UTC), "hi") == "13 सित॰ 2026"
    assert "misleading" not in _summary("misleading", "X", 1, "te")
