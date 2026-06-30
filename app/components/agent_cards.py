import markdown
import streamlit as st
from app.components.styles import severity_badge, category_badge


def _agent_icon(agent_name: str) -> str:
    icons = {
        "classify": "🔍",
        "classification": "🔍",
        "severity": "⚠️",
        "resolution": "🛠️",
        "approval": "👤",
    }
    return icons.get(agent_name.lower(), "🤖")


def _agent_color_class(agent_name: str) -> str:
    names = {
        "classify": "classify",
        "classification": "classify",
        "severity": "severity",
        "resolution": "resolution",
        "approval": "approval",
    }
    return names.get(agent_name.lower(), "")


def _md(text: str) -> str:
    return markdown.markdown(text, extensions=["extra"])


def display_agent_card(
    agent_name: str,
    title: str,
    status: str,
    result: dict | None = None,
    placeholder=None,
):
    icon = _agent_icon(agent_name)
    color_class = _agent_color_class(agent_name)

    status_labels = {
        "pending": ("Pending", "pending"),
        "running": ("Processing...", "running"),
        "completed": ("Complete", "completed"),
        "error": ("Error", "error"),
    }
    status_text, status_class = status_labels.get(status, ("", ""))

    container = placeholder if placeholder is not None else st

    if status == "running":
        with container:
            st.markdown(
                f'<div class="agent-card running"><div class="agent-header">'
                f'<div class="agent-icon {color_class}">{icon}</div>'
                f'<span class="agent-name">{title}</span>'
                f'<span class="agent-status running">{status_text}</span>'
                f"</div></div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**{title}** is analyzing the ticket...  \n_ _")
        return

    if status == "completed" and result is None:
        with container:
            st.markdown(
                f'<div class="agent-card {status_class}"><div class="agent-header">'
                f'<div class="agent-icon {color_class}">{icon}</div>'
                f'<span class="agent-name">{title}</span>'
                f'<span class="agent-status {status_class}">{status_text}</span>'
                f"</div></div>",
                unsafe_allow_html=True,
            )
        return

    card_html = f"""
    <div class="agent-card {status_class}">
        <div class="agent-header">
            <div class="agent-icon {color_class}">{icon}</div>
            <span class="agent-name">{title}</span>
            <span class="agent-status {status_class}">{status_text}</span>
        </div>
    """

    if result:
        card_html += '<div class="agent-thinking">'

        if agent_name.lower() in ("classify", "classification"):
            cat = result.get("category", "N/A")
            conf = result.get("classification_confidence", 0)
            reason = result.get("classification_reasoning", "")
            card_html += f"""
                <div style="margin-bottom:0.5rem;">
                    {category_badge(cat)}
                    <span style="font-size:0.8rem;margin-left:0.5rem;opacity:0.7;">
                        confidence: {conf:.0%}
                    </span>
                </div>
                <div class="label">Reasoning</div>
                <div class="md-content">{_md(reason) if reason else '<em>No additional reasoning provided.</em>'}</div>
            """

        elif agent_name.lower() == "severity":
            sev = result.get("severity", "N/A")
            score = result.get("severity_score", 0)
            reason = result.get("severity_reasoning", "")
            card_html += f"""
                <div style="margin-bottom:0.5rem;">
                    {severity_badge(sev)}
                    <span style="font-size:0.8rem;margin-left:0.5rem;opacity:0.7;">
                        score: {score}/100
                    </span>
                </div>
                <div class="label">Reasoning</div>
                <div class="md-content">{_md(reason) if reason else '<em>No additional reasoning provided.</em>'}</div>
            """

        elif agent_name.lower() == "resolution":
            resolution = result.get("resolution", "")
            eta = result.get("resolution_eta", "")
            sources = result.get("resolution_sources", [])
            card_html += f"""
                <div class="label">Suggested Resolution</div>
                <div class="md-content">{_md(resolution)}</div>
                <div style="display:flex;gap:1rem;font-size:0.8rem;opacity:0.7;margin-top:0.5rem;">
                    <span>⏱ {eta if eta else 'N/A'}</span>
                    <span>📄 {len(sources)} source(s)</span>
                </div>
            """
            if sources:
                card_html += '<div class="label" style="margin-top:0.5rem;">References</div>'
                for s in sources:
                    card_html += f'<div style="font-size:0.8rem;">📎 {s}</div>'

        card_html += "</div>"

    card_html += "</div>"

    if placeholder is not None:
        placeholder.markdown(card_html, unsafe_allow_html=True)
    else:
        st.markdown(card_html, unsafe_allow_html=True)


def display_workflow_connector():
    st.markdown('<div class="workflow-connector">↓</div>', unsafe_allow_html=True)
