import streamlit as st


def approval_panel(state: dict) -> dict | None:
    resolution = state.get("human_edited_resolution") or state.get("resolution", "")
    if not resolution:
        return None

    st.markdown("### Human Approval")
    st.markdown("Review the suggested resolution below and take action.")

    with st.container(border=True):
        st.markdown("**Suggested Resolution**")
        st.markdown(resolution)

        if state.get("resolution_sources"):
            with st.expander("Referenced sources"):
                for s in state["resolution_sources"]:
                    st.markdown(f"- {s}")

        decision = st.radio(
            "Decision",
            ["Approve", "Edit", "Reject", "Keep Open"],
            horizontal=True,
            label_visibility="collapsed",
        )

        edited = None
        feedback = None

        if decision == "Edit":
            edited = st.text_area(
                "Edit resolution",
                value=resolution,
                height=150,
            )
            feedback = st.text_input("Reason for edit (optional)")

        elif decision == "Reject":
            feedback = st.text_input("Reason for rejection", placeholder="Required feedback")
            if st.button("Submit rejection", type="secondary", use_container_width=True):
                return {"decision": "rejected", "edited_resolution": None, "feedback": feedback}

        if decision == "Approve":
            if st.button("✅ Approve Resolution", type="primary", use_container_width=True):
                return {"decision": "approved", "edited_resolution": None, "feedback": None}

        elif decision == "Edit":
            if st.button("💾 Save Edited Resolution", type="primary", use_container_width=True):
                if edited and edited.strip():
                    return {"decision": "edited", "edited_resolution": edited, "feedback": feedback}

        elif decision == "Keep Open":
            if st.button("📂 Save as Open", type="primary", use_container_width=True):
                return {"decision": "open", "edited_resolution": None, "feedback": None}

    return None
