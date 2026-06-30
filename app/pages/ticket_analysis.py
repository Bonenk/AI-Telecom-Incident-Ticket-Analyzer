import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import time

from app.components.page_loader import render_skeleton
from app.components.ticket_selector import ticket_selector
from app.components.agent_cards import display_agent_card, display_workflow_connector
from app.components.approval_panel import approval_panel
from app.workflow.orchestrator import compile_workflow
from app.services.database import TicketDatabase


def render():
    ph = st.empty()
    with ph:
        render_skeleton("Loading Ticket Analysis...")
    ph.empty()

    st.title(" Ticket Analysis")
    st.markdown("Select a ticket and run the AI agent workflow to classify, assess severity, and suggest resolutions.")

    ticket = ticket_selector()

    if not ticket:
        st.info("Select or enter a ticket above to begin.")
        return

    if not ticket.get("subject") or not ticket.get("description"):
        st.warning("Please provide both a subject and description.")
        return

    st.divider()

    col_run, col_clear = st.columns([1, 5])
    with col_run:
        run_btn = st.button(" Run Analysis", type="primary", use_container_width=True)
    with col_clear:
        if st.button("Clear Results", use_container_width=False):
            for key in ["workflow_result", "workflow_done", "human_decision"]:
                st.session_state.pop(key, None)
            st.rerun()

    if run_btn:
        st.session_state["workflow_done"] = False
        st.session_state["workflow_result"] = None
        st.session_state.pop("human_decision", None)

        placeholders = {
            "classify": st.empty(),
            "severity": st.empty(),
            "resolution": st.empty(),
        }

        display_agent_card("classify", "Classification Agent", "running", placeholder=placeholders["classify"])
        time.sleep(0.3)

        graph = compile_workflow()
        config = {"configurable": {"thread_id": f"ticket_{ticket.get('ticket_id', 'custom')}"}}

        initial_state = {
            "ticket": ticket,
            "category": None,
            "classification_confidence": 0.0,
            "classification_reasoning": "",
            "severity": None,
            "severity_score": 0,
            "severity_reasoning": "",
            "resolution": None,
            "resolution_eta": None,
            "resolution_sources": [],
            "route": None,
            "human_decision": None,
            "human_edited_resolution": None,
            "human_feedback": None,
            "error": None,
        }

        try:
            for event in graph.stream(initial_state, config):
                for node_name, node_output in event.items():
                    if node_name == "classify":
                        display_agent_card(
                            "classify", "Classification Agent", "completed",
                            result=node_output, placeholder=placeholders["classify"],
                        )
                        display_workflow_connector()
                        display_agent_card("severity", "Severity Detection Agent", "running", placeholder=placeholders["severity"])
                        time.sleep(0.2)

                    elif node_name == "severity":
                        display_agent_card(
                            "severity", "Severity Detection Agent", "completed",
                            result=node_output, placeholder=placeholders["severity"],
                        )
                        display_workflow_connector()
                        display_agent_card("resolution", "Resolution Suggestion Agent", "running", placeholder=placeholders["resolution"])
                        time.sleep(0.2)

                    elif node_name == "resolution":
                        display_agent_card(
                            "resolution", "Resolution Suggestion Agent", "completed",
                            result=node_output, placeholder=placeholders["resolution"],
                        )

                    elif node_name == "auto_resolve":
                        display_agent_card(
                            "resolution", "Resolution Suggestion Agent", "completed",
                            result={
                                "resolution": node_output.get("resolution", "Auto-resolved."),
                                "resolution_eta": "5 minutes",
                                "resolution_sources": ["auto-billing-rule"],
                            },
                            placeholder=placeholders["resolution"],
                        )

            final_state = None
            for s in graph.get_state_history(config):
                final_state = s.values
                break

            if not final_state:
                final_state = initial_state

            st.session_state["workflow_result"] = final_state
            st.session_state["workflow_done"] = True

        except Exception as e:
            st.error(f"Workflow error: {e}")
            st.exception(e)
            return

    if st.session_state.get("workflow_done") and st.session_state.get("workflow_result"):
        result = st.session_state["workflow_result"]
        existing_decision = st.session_state.get("human_decision")

        display_workflow_connector()

        if existing_decision is None:
            with st.container():
                st.markdown("###  Human Approval Required")
                st.markdown("Review the analysis and resolution below.")

                summary_cols = st.columns(3)
                with summary_cols[0]:
                    cat = result.get("category", "N/A")
                    conf = result.get("classification_confidence", 0)
                    st.markdown(f"**Category:** {cat}")
                    st.markdown(f"*confidence: {conf:.0%}*")
                    st.markdown(f"*{result.get('classification_reasoning', '')}*")
                with summary_cols[1]:
                    sev = result.get("severity", "N/A")
                    score = result.get("severity_score", 0)
                    st.markdown(f"**Severity:** {sev}")
                    st.markdown(f"*score: {score}/100*")
                    st.markdown(f"*{result.get('severity_reasoning', '')}*")
                with summary_cols[2]:
                    st.markdown(f"**Resolution Time:** {result.get('resolution_eta', 'N/A')}")
                    st.markdown(f"**Sources:** {len(result.get('resolution_sources', []))}")

                st.markdown("---")

                decision = approval_panel(result)
                if decision:
                    st.session_state["human_decision"] = decision
                    st.rerun()

        else:
            decision = existing_decision
            db = TicketDatabase()

            ticket_id = ticket.get("ticket_id", "")
            db.delete_open_analyses(ticket_id)

            if decision["decision"] == "open":
                db.save_analysis(result, ticket=ticket)
                st.toast("Ticket saved as Open for follow-up!", icon="📂")
            else:
                st.toast(f"Resolution {decision['decision']}!", icon="✅")
                final_resolution = decision.get("edited_resolution") or result.get("resolution", "")
                st.markdown("### Final Resolution")
                st.markdown(final_resolution)
                db.save_analysis(result, human_decision=decision, ticket=ticket)
            st.cache_data.clear()

            cols = st.columns([1, 1, 4])
            with cols[0]:
                st.download_button(
                    " Download Report",
                    data=_format_report(result, decision, decision.get("edited_resolution") or result.get("resolution", "")),
                    file_name=f"ticket_{ticket.get('ticket_id', 'report')}.md",
                    mime="text/markdown",
                )
            with cols[1]:
                if st.button(" New Analysis", use_container_width=True):
                    for key in ["workflow_result", "workflow_done", "human_decision"]:
                        st.session_state.pop(key, None)
                    st.rerun()


def _format_report(state: dict, decision: dict, resolution: str) -> str:
    lines = [
        "# Telecom Incident Ticket Analysis Report",
        "",
        f"**Ticket ID:** {state.get('ticket', {}).get('ticket_id', 'N/A')}",
        f"**Subject:** {state.get('ticket', {}).get('subject', 'N/A')}",
        "",
        "## Classification",
        f"- **Category:** {state.get('category', 'N/A')}",
        f"- **Confidence:** {state.get('classification_confidence', 0):.0%}",
        f"- **Reasoning:** {state.get('classification_reasoning', '')}",
        "",
        "## Severity Assessment",
        f"- **Severity:** {state.get('severity', 'N/A')}",
        f"- **Score:** {state.get('severity_score', 0)}/100",
        f"- **Reasoning:** {state.get('severity_reasoning', '')}",
        "",
        "## Resolution",
        f"{resolution}",
        "",
        f"**Estimated Time:** {state.get('resolution_eta', 'N/A')}",
        f"**Sources:** {', '.join(state.get('resolution_sources', []))}",
        "",
        "## Human Decision",
        f"- **Decision:** {decision.get('decision', 'N/A')}",
    ]
    if decision.get("feedback"):
        lines.append(f"- **Feedback:** {decision['feedback']}")
    lines.extend(["", "---", "*Generated by AI Telecom Incident Ticket Analyzer*"])
    return "\n".join(lines)


render()
