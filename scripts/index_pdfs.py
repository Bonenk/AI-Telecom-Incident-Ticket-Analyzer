import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import AppConfig
from app.rag.document_loader import load_and_chunk_pdfs
from app.rag.vector_store import index_documents
from app.services.database import TicketDatabase


def main():
    cfg = AppConfig()
    db = TicketDatabase()

    print(f"Loading PDFs from {cfg.pdfs_dir}...")
    docs = load_and_chunk_pdfs(cfg.pdfs_dir)
    if not docs:
        print("  No PDFs found.")
        return

    print(f"  Loaded {len(docs)} chunks from {len(list(cfg.pdfs_dir.glob('*.pdf')))} PDFs")

    print("Indexing into vector store...")
    index_documents(docs, "telecom_pdfs")
    print(f"  Indexed {len(docs)} chunks")

    print("Tracking PDFs in database...")
    for pdf_file in sorted(cfg.pdfs_dir.glob("*.pdf")):
        db.save_pdf_document(
            filename=pdf_file.name,
            file_size=pdf_file.stat().st_size,
            chunk_count=0,
            source="synthetic",
        )

    print("\nDone!")


if __name__ == "__main__":
    main()
