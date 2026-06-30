import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import patch, MagicMock

from app.rag.retriever import format_docs, build_rag_chain, query_troubleshooting
from app.rag.vector_store import get_vector_store, index_documents


class TestFormatDocs:
    def test_format_docs_empty(self):
        assert format_docs([]) == ""

    def test_format_docs_single(self):
        doc = MagicMock()
        doc.metadata = {"source": "guide.pdf"}
        doc.page_content = "Step 1: Reboot"
        result = format_docs([doc])
        assert "[guide.pdf]" in result
        assert "Step 1: Reboot" in result

    def test_format_docs_multiple(self):
        docs = []
        for name in ["a.pdf", "b.pdf"]:
            d = MagicMock()
            d.metadata = {"source": name}
            d.page_content = f"Content from {name}"
            docs.append(d)
        result = format_docs(docs)
        assert "[a.pdf]" in result
        assert "[b.pdf]" in result
        assert "Content from a.pdf" in result
        assert "Content from b.pdf" in result


class TestRagChain:
    @patch("app.rag.retriever.LLMFactory.get_llm")
    @patch("app.rag.retriever.get_retriever")
    def test_build_rag_chain(self, mock_get_retriever, mock_get_llm):
        mock_llm = MagicMock()
        mock_llm.return_value = "Check the fiber connection"
        mock_llm.invoke.return_value = "Check the fiber connection"
        mock_get_llm.return_value = mock_llm

        mock_retriever = MagicMock()
        mock_doc = MagicMock()
        mock_doc.metadata = {"source": "fiber.pdf"}
        mock_doc.page_content = "Fiber troubleshooting steps"
        mock_retriever.invoke.return_value = [mock_doc]
        mock_get_retriever.return_value = mock_retriever

        chain = build_rag_chain("test_collection", k=2)
        result = chain.invoke("How to fix fiber?")
        assert "fiber" in result.lower()


class TestVectorStore:
    @patch("app.rag.vector_store._get_embeddings")
    @patch("app.rag.vector_store.Chroma")
    def test_get_vector_store(self, mock_chroma, mock_emb):
        mock_emb.return_value = MagicMock()
        mock_chroma.return_value = MagicMock()
        store = get_vector_store("test_collection", persist_directory="/tmp/test_chroma")
        assert store is not None

    @patch("app.rag.vector_store.Chroma")
    @patch("app.rag.vector_store.get_vector_store")
    def test_index_documents(self, mock_get_store, mock_chroma):
        mock_store = MagicMock()
        mock_store.get.return_value = {"ids": []}
        mock_get_store.return_value = mock_store

        from langchain_core.documents import Document
        docs = [Document(page_content="test", metadata={"source": "test.pdf"})]
        result = index_documents(docs, "test_collection", "/tmp/test_chroma")
        assert result is not None
