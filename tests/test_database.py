import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import patch
from app.services.database import TicketDatabase


@pytest.fixture
def db(tmp_path):
    return TicketDatabase(db_path=tmp_path / "test.db")


class TestTicketDatabase:
    def test_init_creates_table(self, db):
        with patch("app.services.database.TicketDatabase._init_db") as mock_init:
            TicketDatabase(db_path=db.db_path)
            mock_init.assert_called_once()

    def test_save_and_list(self, db):
        state = {
            "category": "Network",
            "classification_confidence": 0.95,
            "classification_reasoning": "Outage symptoms",
            "severity": "Critical",
            "severity_score": 90,
            "severity_reasoning": "Full outage",
            "resolution": "Reboot router",
            "resolution_eta": "30 minutes",
            "resolution_sources": ["guide.pdf"],
        }
        ticket = {"ticket_id": "TKT-001", "subject": "Down", "description": "No connection"}
        decision = {"decision": "approved", "edited_resolution": None, "feedback": "Looks good"}

        row_id = db.save_analysis(state, human_decision=decision, ticket=ticket)
        assert row_id > 0

        analyses = db.list_analyses()
        assert len(analyses) == 1
        assert analyses[0]["ticket_id"] == "TKT-001"
        assert analyses[0]["category"] == "Network"
        assert analyses[0]["human_decision"] == "approved"
        assert analyses[0]["resolution_sources"] == ["guide.pdf"]

    def test_get_analysis(self, db):
        state = {"category": "Billing", "classification_confidence": 0.8, "resolution": "Refund"}
        ticket = {"ticket_id": "TKT-002", "subject": "Overcharge", "description": ""}
        decision = {"decision": "edited", "edited_resolution": "Partial refund", "feedback": ""}

        row_id = db.save_analysis(state, human_decision=decision, ticket=ticket)
        got = db.get_analysis(row_id)
        assert got is not None
        assert got["ticket_id"] == "TKT-002"
        assert got["resolution"] == "Partial refund"
        assert got["human_decision"] == "edited"

    def test_get_analysis_not_found(self, db):
        assert db.get_analysis(999) is None

    def test_delete_analysis(self, db):
        row_id = db.save_analysis({}, ticket={"ticket_id": "TKT-003"})
        assert db.delete_analysis(row_id) is True
        assert db.get_analysis(row_id) is None

    def test_delete_analysis_not_found(self, db):
        assert db.delete_analysis(999) is False

    def test_update_analysis(self, db):
        row_id = db.save_analysis(
            {"category": "Network", "resolution": "Reboot"},
            ticket={"ticket_id": "TKT-004"},
        )
        ok = db.update_analysis(row_id, {
            "human_decision": "approved",
            "human_feedback": "Looks good",
        })
        assert ok is True
        got = db.get_analysis(row_id)
        assert got["human_decision"] == "approved"
        assert got["human_feedback"] == "Looks good"

    def test_update_analysis_not_found(self, db):
        ok = db.update_analysis(999, {"human_decision": "approved"})
        assert ok is False

    def test_update_analysis_no_allowed_fields(self, db):
        row_id = db.save_analysis({}, ticket={"ticket_id": "TKT-005"})
        ok = db.update_analysis(row_id, {"ticket_id": "hack"})
        assert ok is False

    def test_count_analyses(self, db):
        assert db.count_analyses() == 0
        db.save_analysis({"category": "Network"}, ticket={"ticket_id": "T1"})
        db.save_analysis({"category": "Billing"}, ticket={"ticket_id": "T2"})
        assert db.count_analyses() == 2

    def test_no_human_decision(self, db):
        row_id = db.save_analysis({"category": "Network"}, ticket={"ticket_id": "TKT-NO-HD"})
        got = db.get_analysis(row_id)
        assert got["resolution"] == ""
        assert got["human_decision"] is None

    def test_delete_open_analyses(self, db):
        id1 = db.save_analysis({}, ticket={"ticket_id": "TKT-OPEN"})
        id2 = db.save_analysis({"category": "Billing"}, ticket={"ticket_id": "TKT-OPEN"}, human_decision={"decision": "approved"})
        id3 = db.save_analysis({}, ticket={"ticket_id": "TKT-OTHER"})
        assert db.count_analyses() == 3
        deleted = db.delete_open_analyses("TKT-OPEN")
        assert deleted == 1
        assert db.get_analysis(id1) is None
        assert db.get_analysis(id2) is not None
        assert db.get_analysis(id3) is not None

    def test_list_empty(self, db):
        assert db.list_analyses() == []
