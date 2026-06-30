import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import AppConfig
from app.data.synthetic_generator import generate_tickets, generate_outage_logs
from app.data.pdf_generator import generate_pdfs
from app.services.database import TicketDatabase
from app.rag.document_loader import load_and_chunk_pdfs
from app.rag.vector_store import index_documents


def main():
    cfg = AppConfig()
    db = TicketDatabase()

    print(f"Generating {cfg.ticket_count} synthetic tickets...")
    tickets = generate_tickets(cfg.ticket_count)

    print("Generating 50 outage logs...")
    logs = generate_outage_logs(50)

    print("Seeding database...")
    db.seed_synthetic_data(tickets, logs)
    print(f"  -> {cfg.db_path}")

    print("Generating 20 troubleshooting PDFs via LLM...")
    titles = generate_pdfs(cfg.pdfs_dir, force=False)

    print("Indexing PDFs into vector store...")
    docs = load_and_chunk_pdfs(cfg.pdfs_dir)
    if docs:
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
    print(f"  Tickets: {len(tickets)}")
    print(f"  Outage logs: {len(logs)}")
    print(f"  PDFs: {len(titles)}")


if __name__ == "__main__":
    main()
