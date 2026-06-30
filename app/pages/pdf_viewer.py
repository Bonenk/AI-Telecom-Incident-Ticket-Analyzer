import sys
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

from app.config import AppConfig
from app.rag.document_loader import load_pdf, load_and_chunk_pdfs
from app.rag.vector_store import index_documents, get_vector_store
from app.components.page_loader import render_skeleton
from app.services.database import TicketDatabase
from app.services.s3_service import S3Service

cfg = AppConfig()


def _s3() -> S3Service | None:
    try:
        return S3Service()
    except Exception as e:
        st.warning(f"S3 unavailable ({e}) — some features disabled.")
        return None


def _list_from_s3(s3: S3Service) -> list[str]:
    keys = s3.list_files(prefix="pdfs/")
    return sorted(Path(k).name for k in keys if k.lower().endswith(".pdf"))


@st.cache_data
def list_pdfs():
    s3 = _s3()
    if s3 is None:
        return []
    return _list_from_s3(s3)


@st.cache_data
def read_pdf_text(filename: str) -> str:
    s3 = _s3()
    if s3 is None:
        return ""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / filename
        try:
            s3.download_file(f"pdfs/{filename}", tmp_path)
            return load_pdf(str(tmp_path))
        except Exception:
            return ""


def get_chunk_count() -> int:
    store = get_vector_store("telecom_pdfs")
    col = store.get()
    return len(col.get("ids", []))


def get_pdf_docs():
    db = TicketDatabase()
    return db.list_pdf_documents()


def _index_from_directory(directory: str | Path) -> int:
    docs = load_and_chunk_pdfs(directory)
    if not docs:
        return 0
    index_documents(docs, "telecom_pdfs")
    st.cache_data.clear()
    return len(docs)


def reindex_all_from_s3() -> int:
    s3 = _s3()
    if s3 is None:
        return 0
    keys = _list_from_s3(s3)
    if not keys:
        return 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for name in keys:
            s3.download_file(f"pdfs/{name}", Path(tmpdir) / name)
        return _index_from_directory(tmpdir)


def upload_and_index_all(uploaded_files: list) -> int:
    s3 = _s3()
    if s3 is None:
        return 0

    db = TicketDatabase()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        for f in uploaded_files:
            with open(tmp_path / f.name, "wb") as fp:
                fp.write(f.getbuffer())

        s3_keys = [k for k in s3.list_files(prefix="pdfs/") if k.lower().endswith(".pdf")]

        if s3_keys:
            for key in s3_keys:
                s3.download_file(key, tmp_path / Path(key).name)

        total = _index_from_directory(tmpdir)

        for f in uploaded_files:
            _upload_to_s3(s3, tmp_path / f.name)
            existing = {d["filename"] for d in db.list_pdf_documents()}
            if f.name not in existing:
                db.save_pdf_document(
                    filename=f.name,
                    file_size=(tmp_path / f.name).stat().st_size,
                    chunk_count=get_chunk_count(),
                    source="s3",
                )

    return total


def _upload_to_s3(s3: S3Service, local_path: Path):
    try:
        s3.upload_file(local_path, f"pdfs/{local_path.name}")
    except Exception as e:
        st.error(f"Failed to upload {local_path.name} to S3: {e}")


def _delete_from_s3(s3: S3Service, filename: str) -> bool:
    try:
        s3.delete_file(f"pdfs/{filename}")
        return True
    except Exception as e:
        st.error(f"Failed to delete {filename} from S3: {e}")
        return False


def render():
    ph = st.empty()
    with ph:
        render_skeleton("Loading PDFs...")

    pdf_names = list_pdfs()
    chunk_count = get_chunk_count()
    pdf_docs = get_pdf_docs()
    ph.empty()

    st.title(" Knowledge Base")
    st.markdown("Central repository of telecom troubleshooting guides used for **RAG retrieval** during ticket resolution. Browse, upload, and manage documents — all stored in **S3-compatible storage**.")

    tab_browse, tab_upload, tab_tracking = st.tabs(["Browse Knowledge Base", "Add & Index", "Document Registry"])

    with tab_browse:
        if not pdf_names:
            st.warning("No PDFs found in S3. Use the Add & Index tab to upload.")
        else:
            selected_name = st.selectbox(
                "Select a troubleshooting guide", pdf_names,
                key="pdf_selector",
            )
            if selected_name:
                text = read_pdf_text(selected_name)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### Document Info")
                    st.markdown(f"**File:** {selected_name}")
                    st.markdown(f"**Characters:** {len(text):,}")
                    s3 = _s3()
                    if s3 is not None:
                        with tempfile.TemporaryDirectory() as tmpdir:
                            tmp_path = Path(tmpdir) / selected_name
                            try:
                                s3.download_file(f"pdfs/{selected_name}", tmp_path)
                                with open(tmp_path, "rb") as f:
                                    st.download_button(
                                        " Download PDF", data=f, file_name=selected_name,
                                        mime="application/pdf", use_container_width=True,
                                    )
                            except Exception:
                                pass
                with col2:
                    st.markdown("### Indexing Status")
                    st.metric("Chunks in Vector Store", chunk_count)
                    if chunk_count > 0:
                        st.success("PDFs indexed and available for RAG retrieval.")
                    else:
                        st.warning("No indexed chunks. Use the Add & Index tab to index PDFs.")

                st.divider()
                st.markdown("### Extracted Content")
                with st.container(border=True, height=500):
                    st.markdown(text)

    with tab_upload:
        st.markdown("### Add Documents")
        st.markdown("Upload one or more troubleshooting guides. Files are stored in **S3** and indexed into ChromaDB for RAG retrieval.")

        uploaded_files = st.file_uploader(
            "Choose PDF file(s)", type=["pdf"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            st.markdown(f"{len(uploaded_files)} file(s) selected:")
            for f in uploaded_files:
                st.markdown(f"- {f.name}")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(" Upload, Index & Save to S3", type="primary", use_container_width=True):
                    with st.spinner(f"Indexing {len(uploaded_files)} PDF(s) and uploading to S3..."):
                        count = upload_and_index_all(uploaded_files)
                        if count > 0:
                            st.success(f"Uploaded {len(uploaded_files)} file(s) to S3 and indexed ({count} total chunks).")
                            st.rerun()
                        else:
                            st.error("Failed to process PDFs.")
            with col_b:
                if st.button("Cancel", use_container_width=True):
                    st.rerun()

        st.divider()
        st.markdown("### Re-index All Documents")

        if st.button(" Re-index All from S3", type="secondary", use_container_width=True):
            with st.spinner("Downloading all PDFs from S3 and re-indexing..."):
                count = reindex_all_from_s3()
                if count > 0:
                    st.success(f"Re-indexed {count} chunks from S3.")
                    st.rerun()
                else:
                    st.warning("No PDFs found in S3 to index.")

    with tab_tracking:
        st.markdown("### Document Registry")
        st.markdown("All registered knowledge base documents stored in **S3**.")

        if pdf_docs:
            data = []
            for d in pdf_docs:
                data.append({
                    "Filename": d["filename"],
                    "Size (bytes)": d["file_size"],
                    "Source": d.get("source", "s3"),
                    "Uploaded": d.get("uploaded_at", ""),
                })

            st.dataframe(data, use_container_width=True, hide_index=True)

            col_del, _ = st.columns([1, 5])
            with col_del:
                filenames = [d["filename"] for d in pdf_docs]
                del_name = st.selectbox("Delete document", filenames, key="del_pdf")
                if st.button(" Delete from S3 & Registry", use_container_width=True, type="secondary"):
                    s3 = _s3()
                    db = TicketDatabase()
                    if s3 is not None:
                        _delete_from_s3(s3, del_name)
                    db.delete_pdf_document(del_name)
                    reindex_all_from_s3()
                    st.success(f"Deleted {del_name} from S3 and re-indexed.")
                    st.rerun()
        else:
            st.info("No PDF documents registered. Upload PDFs or run `uv run python scripts/generate_data.py` first.")


render()
