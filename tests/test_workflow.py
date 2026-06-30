import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import patch, MagicMock

from app.workflow.orchestrator import (
    build_workflow,
    compile_workflow,
    AgentState,
    classification_node,
    severity_node,
    resolution_node,
    auto_resolve_node,
    route_ticket,
)


class TestWorkflowNodes:
    def test_auto_resolve_node(self):
        result = auto_resolve_node(AgentState(
            ticket={},
            category=None,
            classification_confidence=0.0,
            classification_reasoning="",
            severity=None,
            severity_score=0,
            severity_reasoning="",
            resolution=None,
            resolution_eta=None,
            resolution_sources=[],
            route=None,
            human_decision=None,
            human_edited_resolution=None,
            human_feedback=None,
            error=None,
        ))
        assert "Auto-resolved" in result["resolution"]
        assert result["resolution_eta"] == "5 minutes"
        assert "auto-billing-rule" in result["resolution_sources"]

    @patch("app.workflow.orchestrator.classify_ticket")
    def test_classification_node(self, mock_classify):
        mock_classify.return_value = {
            "category": "Network",
            "confidence": 0.92,
            "reasoning": "Outage symptoms",
        }
        result = classification_node(AgentState(
            ticket={"subject": "Down", "description": "No connection"},
            category=None,
            classification_confidence=0.0,
            classification_reasoning="",
            severity=None,
            severity_score=0,
            severity_reasoning="",
            resolution=None,
            resolution_eta=None,
            resolution_sources=[],
            route=None,
            human_decision=None,
            human_edited_resolution=None,
            human_feedback=None,
            error=None,
        ))
        assert result["category"] == "Network"
        assert result["classification_confidence"] == 0.92

    @patch("app.workflow.orchestrator.detect_severity")
    def test_severity_node(self, mock_severity):
        mock_severity.return_value = {
            "severity": "Critical",
            "score": 90,
            "reasoning": "Full outage",
        }
        result = severity_node(AgentState(
            ticket={"subject": "Down", "description": "No connection"},
            category="Network",
            classification_confidence=0.92,
            classification_reasoning="",
            severity=None,
            severity_score=0,
            severity_reasoning="",
            resolution=None,
            resolution_eta=None,
            resolution_sources=[],
            route=None,
            human_decision=None,
            human_edited_resolution=None,
            human_feedback=None,
            error=None,
        ))
        assert result["severity"] == "Critical"
        assert result["severity_score"] == 90


class TestRouter:
    def test_route_auto_resolve(self):
        state = {"severity": "Low", "category": "Billing"}
        assert route_ticket(state) == "auto_resolve"

    def test_route_normal_resolution(self):
        state = {"severity": "High", "category": "Network"}
        assert route_ticket(state) == "resolution"

    def test_route_resolution_with_empty_severity(self):
        state = {"severity": "", "category": "Billing"}
        assert route_ticket(state) == "resolution"

    def test_route_case_insensitive(self):
        state = {"severity": "LOW", "category": "BILLING"}
        assert route_ticket(state) == "auto_resolve"


class TestWorkflowGraph:
    def test_build_workflow(self):
        graph = build_workflow()
        nodes = [n for n in graph.nodes]
        assert "classify" in nodes
        assert "severity" in nodes
        assert "resolution" in nodes
        assert "auto_resolve" in nodes

    def test_compile_workflow(self):
        app = compile_workflow()
        assert app is not None

    def test_auto_resolve_route(self):
        app = compile_workflow()
        ticket = {
            "ticket_id": "TKT-001",
            "subject": "Small billing overcharge",
            "description": "$5 overcharge on last bill",
        }
        config = {"configurable": {"thread_id": "test-001"}}
        initial = AgentState(
            ticket=ticket,
            category=None,
            classification_confidence=0.0,
            classification_reasoning="",
            severity=None,
            severity_score=0,
            severity_reasoning="",
            resolution=None,
            resolution_eta=None,
            resolution_sources=[],
            route=None,
            human_decision=None,
            human_edited_resolution=None,
            human_feedback=None,
            error=None,
        )
        # Override routers and nodes with mocks
        with (
            patch("app.workflow.orchestrator.classify_ticket") as mock_c,
            patch("app.workflow.orchestrator.detect_severity") as mock_s,
        ):
            mock_c.return_value = {"category": "Billing", "confidence": 0.9, "reasoning": ""}
            mock_s.return_value = {"severity": "Low", "score": 20, "reasoning": ""}
            result = app.invoke(initial, config)

        assert result["category"] == "Billing"
        assert result["severity"] == "Low"
        assert "Auto-resolved" in result["resolution"]
