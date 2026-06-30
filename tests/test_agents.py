import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import pytest
from unittest.mock import patch, MagicMock

from app.agents.classification_agent import classify_ticket, _parse_json as parse_classification
from app.agents.severity_agent import detect_severity, _parse_json as parse_severity
from app.agents.resolution_agent import suggest_resolution, _parse_json as parse_resolution
from app.agents.human_approval_agent import format_for_human, process_human_decision


class TestClassificationAgent:
    def test_parse_json_valid(self):
        raw = '{"category": "Network", "confidence": 0.9, "reasoning": "test"}'
        result = parse_classification(raw)
        assert result["category"] == "Network"
        assert result["confidence"] == 0.9

    def test_parse_json_with_code_fences(self):
        raw = '```json\n{"category": "Billing", "confidence": 0.8, "reasoning": "test"}\n```'
        result = parse_classification(raw)
        assert result["category"] == "Billing"

    def test_parse_json_fallback(self):
        result = parse_classification("not json")
        assert result["category"] == "Customer"

    @patch("app.agents.classification_agent.LLMFactory.get_llm")
    def test_classify_ticket(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.return_value = '{"category": "Network", "confidence": 0.95, "reasoning": "check"}'
        mock_llm.invoke.return_value = '{"category": "Network", "confidence": 0.95, "reasoning": "check"}'
        mock_get_llm.return_value = mock_llm

        ticket = {"subject": "Outage", "description": "No connectivity"}
        result = classify_ticket(ticket)
        assert result["category"] == "Network"
        assert result["confidence"] == 0.95


class TestSeverityAgent:
    def test_parse_json_valid(self):
        raw = '{"severity": "Critical", "score": 95, "reasoning": "outage"}'
        result = parse_severity(raw)
        assert result["severity"] == "Critical"
        assert result["score"] == 95

    def test_parse_json_fallback(self):
        result = parse_severity("bad")
        assert result["severity"] == "Medium"
        assert result["score"] == 50

    @patch("app.agents.severity_agent.LLMFactory.get_llm")
    def test_detect_severity(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.return_value = '{"severity": "High", "score": 75, "reasoning": "partial outage"}'
        mock_llm.invoke.return_value = '{"severity": "High", "score": 75, "reasoning": "partial outage"}'
        mock_get_llm.return_value = mock_llm

        result = detect_severity({"subject": "Slow internet", "description": "High latency"}, "Network")
        assert result["severity"] == "High"
        assert result["score"] == 75


class TestResolutionAgent:
    def test_parse_json_valid(self):
        raw = '{"resolution": "Reboot router", "estimated_time": "30 minutes", "references": ["guide.pdf"]}'
        result = parse_resolution(raw)
        assert "Reboot" in result["resolution"]
        assert result["estimated_time"] == "30 minutes"
        assert "guide.pdf" in result["references"]

    def test_parse_json_fallback(self):
        result = parse_resolution("garbage")
        assert "Investigate" in result["resolution"]
        assert result["estimated_time"] == "TBD"

    @patch("app.agents.resolution_agent.LLMFactory.get_llm")
    @patch("app.agents.resolution_agent.get_retriever")
    def test_suggest_resolution(self, mock_get_retriever, mock_get_llm):
        mock_llm = MagicMock()
        expected = '{"resolution": "Check fiber connection", "estimated_time": "1 hour", "references": ["fiber_guide.pdf"]}'
        mock_llm.return_value = expected
        mock_llm.invoke.return_value = expected
        mock_get_llm.return_value = mock_llm

        mock_retriever = MagicMock()
        mock_retriever.invoke.return_value = [MagicMock(page_content="content", metadata={"source": "fiber_guide.pdf"})]
        mock_get_retriever.return_value = mock_retriever

        ticket = {"subject": "Fiber down", "description": "No light"}
        result = suggest_resolution(ticket, "Network", "Critical")
        assert "fiber" in result["resolution"].lower()
        assert "fiber_guide.pdf" in result["references"]


class TestHumanApprovalAgent:
    def test_format_for_human(self):
        state = {
            "ticket": {"ticket_id": "TKT-001", "subject": "Outage"},
            "category": "Network",
            "classification_confidence": 0.9,
            "severity": "Critical",
            "severity_score": 95,
            "resolution": "Do X",
            "resolution_sources": ["doc.pdf"],
        }
        result = format_for_human(state)
        assert result["ticket_id"] == "TKT-001"
        assert result["resolution"] == "Do X"
        assert result["sources"] == ["doc.pdf"]

    def test_process_human_decision_approved(self):
        state = {}
        decision = {"decision": "approved", "edited_resolution": None, "feedback": "Looks good"}
        result = process_human_decision(state, decision)
        assert result["human_decision"] == "approved"
        assert result["human_feedback"] == "Looks good"

    def test_process_human_decision_edited(self):
        state = {}
        decision = {"decision": "edited", "edited_resolution": "Updated resolution", "feedback": "Fixed"}
        result = process_human_decision(state, decision)
        assert result["human_decision"] == "edited"
        assert result["human_edited_resolution"] == "Updated resolution"

    def test_process_human_decision_rejected(self):
        state = {}
        decision = {"decision": "rejected", "edited_resolution": None, "feedback": "Wrong category"}
        result = process_human_decision(state, decision)
        assert result["human_decision"] == "rejected"
        assert "edited_resolution" not in result
