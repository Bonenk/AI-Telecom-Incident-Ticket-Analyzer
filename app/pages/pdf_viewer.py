import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from app.config import AppConfig
from app.rag.document_loader import load_pdf, load_and_chunk_pdfs
from app.rag.vector_store import index_documents, get_vector_store
from app.components.page_loader import render_skeleton
from app.services.database import TicketDatabase

cfg = AppConfig()


@st.cache_data
def list_pdfs():
    return sorted(cfg.pdfs_dir.glob("*.pdf"))


@st.cache_data
def read_pdf_text(path: str) -> str:
    return load_pdf(path)


def get_chunk_count() -> int:
    store = get_vector_store("telecom_pdfs")
    collection = store.get()
    return len(collection.get("ids", []))


def get_pdf_docs():
    db = TicketDatabase()
    return db.list_pdf_documents()


def reindex_all():
    docs = load_and_chunk_pdfs(cfg.pdfs_dir)
    if not docs:
        return 0
    index_documents(docs, "telecom_pdfs")
    st.cache_data.clear()

    db = TicketDatabase()
    chunk_count = get_chunk_count()
    for pdf_file in sorted(cfg.pdfs_dir.glob("*.pdf")):
        existing = db.list_pdf_documents()
        exists = any(d["filename"] == pdf_file.name for d in existing)
        if not exists:
            db.save_pdf_document(
                filename=pdf_file.name,
                file_size=pdf_file.stat().st_size,
                chunk_count=chunk_count,
                source="manual",
            )
        else:
            db.save_pdf_document(
                filename=pdf_file.name,
                file_size=pdf_file.stat().st_size,
                chunk_count=chunk_count,
                source="manual",
            )
    return len(docs)


def upload_and_index(uploaded_file) -> int:
    pdf_path = cfg.pdfs_dir / uploaded_file.name
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    docs = load_and_chunk_pdfs(cfg.pdfs_dir)
    if not docs:
        return 0
    index_documents(docs, "telecom_pdfs")
    st.cache_data.clear()

    db = TicketDatabase()
    chunk_count = get_chunk_count()
    db.save_pdf_document(
        filename=uploaded_file.name,
        file_size=pdf_path.stat().st_size,
        chunk_count=chunk_count,
        source="manual",
    )
    return len(docs)


def render():
    ph = st.empty()
    with ph:
        render_skeleton("Loading PDFs...")

    pdf_files = list_pdfs()
    chunk_count = get_chunk_count()
    pdf_docs = get_pdf_docs()
    ph.empty()

    st.title(" Knowledge Base")
    st.markdown("Central repository of telecom troubleshooting guides used for **RAG retrieval** during ticket resolution. Browse existing documents, upload new guides, and manage the document registry.")

    tab_browse, tab_upload, tab_tracking = st.tabs(["Browse Knowledge Base", "Add & Index", "Document Registry"])

    with tab_browse:
        if not pdf_files:
            st.warning("No PDFs found. Use the Upload & Index tab to add PDFs.")
        else:
            selected_name = st.selectbox(
                "Select a troubleshooting guide", [p.name for p in pdf_files],
                key="pdf_selector",
            )
            if selected_name:
                pdf_path = cfg.pdfs_dir / selected_name
                text = read_pdf_text(str(pdf_path))

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### Document Info")
                    st.markdown(f"**File:** {selected_name}")
                    st.markdown(f"**Size:** {pdf_path.stat().st_size:,} bytes")
                    st.markdown(f"**Characters:** {len(text):,}")
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            " Download PDF", data=f, file_name=selected_name,
                            mime="application/pdf", use_container_width=True,
                        )
                with col2:
                    st.markdown("### Indexing Status")
                    st.metric("Chunks in Vector Store", chunk_count)
                    if chunk_count > 0:
                        st.success("PDFs indexed and available for RAG retrieval.")
                    else:
                        st.warning("No indexed chunks. Use the Upload & Index tab to index PDFs.")

                st.divider()
                st.markdown("### Extracted Content")
                with st.container(border=True, height=500):
                    st.markdown(text)

    with tab_upload:
        st.markdown("### Add Document")
        st.markdown("Upload a new troubleshooting guide to expand the knowledge base.")

        uploaded_file = st.file_uploader(
            "Choose a PDF file", type=["pdf"],
            accept_multiple_files=False,
        )

        if uploaded_file:
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(" Save & Index", type="primary", use_container_width=True):
                    with st.spinner("Indexing PDF..."):
                        count = upload_and_index(uploaded_file)
                        if count > 0:
                            st.success(f"Uploaded and indexed ({count} chunks created). Track it in Document Registry.")
                            st.rerun()
                        else:
                            st.error("Failed to index PDF.")
            with col_b:
                if st.button("Cancel", use_container_width=True):
                    st.rerun()

        st.divider()
        st.markdown("### Re-index All Documents")

        if st.button(" Re-index All", type="secondary", use_container_width=True):
            with st.spinner("Re-indexing all PDFs..."):
                count = reindex_all()
                if count > 0:
                    st.success(f"Re-indexed {count} chunks from {len(pdf_files)} PDFs.")
                    st.rerun()
                else:
                    st.warning("No PDFs found to index.")

    with tab_tracking:
        st.markdown("### Document Registry")
        st.markdown("All registered knowledge base documents with indexing status.")

        if pdf_docs:
            data = []
            for d in pdf_docs:
                data.append({
                    "Filename": d["filename"],
                    "Size (bytes)": d["file_size"],
                    "Source": d.get("source", "manual"),
                    "Uploaded": d.get("uploaded_at", ""),
                })

            st.dataframe(data, use_container_width=True, hide_index=True)

            col_del, _ = st.columns([1, 5])
            with col_del:
                filenames = [d["filename"] for d in pdf_docs]
                del_name = st.selectbox("Delete document entry", filenames, key="del_pdf")
                if st.button(" Delete from Registry", use_container_width=True, type="secondary"):
                    db = TicketDatabase()
                    db.delete_pdf_document(del_name)
                    st.rerun()
        else:
            st.info("No PDF documents registered. Upload PDFs or run `uv run python scripts/generate_data.py` first.")


render()
