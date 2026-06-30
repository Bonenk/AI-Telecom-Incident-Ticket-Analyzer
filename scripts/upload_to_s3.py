import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import AppConfig
from app.services.s3_service import S3Service
from app.services.database import TicketDatabase


def main():
    cfg = AppConfig()
    s3 = S3Service()
    db = TicketDatabase()
    pdfs_dir = cfg.pdfs_dir

    if not pdfs_dir.exists():
        print(f"PDFs directory not found: {pdfs_dir}")
        sys.exit(1)

    pdf_files = list(pdfs_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdfs_dir}")
        sys.exit(0)

    print(f"Uploading {len(pdf_files)} PDFs to bucket '{s3.bucket}'...")
    for pdf_path in pdf_files:
        key = f"pdfs/{pdf_path.name}"
        try:
            s3.upload_file(pdf_path, key)
            print(f"  OK  {pdf_path.name} -> {key}")
            db.save_pdf_document(
                filename=pdf_path.name,
                file_size=pdf_path.stat().st_size,
                source="s3-uploaded",
            )
        except Exception as e:
            print(f"  FAIL {pdf_path.name}: {e}")

    print("\nUpload complete.")


if __name__ == "__main__":
    main()
