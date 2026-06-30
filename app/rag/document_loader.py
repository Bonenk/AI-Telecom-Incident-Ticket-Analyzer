from pathlib import Path
from typing import Iterator
import fitz
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import AppConfig


def load_pdf(file_path: str | Path) -> str:
    path = Path(file_path)
    text_parts = []
    with fitz.open(str(path)) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def load_pdfs_from_dir(directory: str | Path) -> list[tuple[str, str]]:
    dir_path = Path(directory)
    results = []
    for pdf_file in sorted(dir_path.glob("*.pdf")):
        text = load_pdf(pdf_file)
        results.append((pdf_file.name, text))
    return results


def chunk_documents(
    raw_docs: list[tuple[str, str]],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    documents = []
    for filename, text in raw_docs:
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={"source": filename, "chunk": i},
                )
            )
    return documents


def load_and_chunk_pdfs(
    directory: str | Path | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[Document]:
    cfg = AppConfig()
    dir_path = Path(directory) if directory else cfg.pdfs_dir
    raw = load_pdfs_from_dir(dir_path)
    return chunk_documents(raw, chunk_size, chunk_overlap)
