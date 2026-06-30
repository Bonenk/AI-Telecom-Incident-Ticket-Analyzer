from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

from app.config import AppConfig, LLMConfig, EmbeddingsConfig

_EMBEDDING_CACHE: dict[str, Embeddings] = {}


def _get_embeddings() -> Embeddings:
    key = "embeddings"
    if key in _EMBEDDING_CACHE:
        return _EMBEDDING_CACHE[key]

    emb_cfg = EmbeddingsConfig()
    llm_cfg = LLMConfig()

    match emb_cfg.provider:
        case "openai":
            from langchain_openai import OpenAIEmbeddings
            _EMBEDDING_CACHE[key] = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=llm_cfg.openai_api_key,
            )
        case "openrouter":
            from langchain_openai import OpenAIEmbeddings
            _EMBEDDING_CACHE[key] = OpenAIEmbeddings(
                model=emb_cfg.openrouter_model,
                api_key=llm_cfg.openrouter_api_key,
                base_url=llm_cfg.openrouter_base_url,
            )
        case _:
            from langchain_huggingface import HuggingFaceEmbeddings
            _EMBEDDING_CACHE[key] = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
            )
    return _EMBEDDING_CACHE[key]


def get_vector_store(
    collection_name: str = "telecom_pdfs",
    persist_directory: str | Path | None = None,
) -> Chroma:
    cfg = AppConfig()
    persist = Path(persist_directory) if persist_directory else cfg.chroma_db_path
    persist.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=collection_name,
        embedding_function=_get_embeddings(),
        persist_directory=str(persist),
    )


def index_documents(
    documents: list[Document],
    collection_name: str = "telecom_pdfs",
    persist_directory: str | Path | None = None,
) -> Chroma:
    store = get_vector_store(collection_name, persist_directory)
    existing = store.get()["ids"]
    if existing:
        store.delete(existing)
    store.add_documents(documents)
    return store
