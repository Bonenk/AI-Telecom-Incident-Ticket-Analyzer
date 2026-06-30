from langchain_chroma import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.rag.vector_store import get_vector_store
from app.services.llm_service import LLMFactory

RAG_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a telecom troubleshooting expert. Use the provided context from "
        "troubleshooting guides to answer the question. If the context does not "
        "contain enough information, say so clearly.\n\nContext:\n{context}",
    ),
    ("human", "{question}"),
])


def get_retriever(collection_name: str = "telecom_pdfs", k: int = 4):
    store: Chroma = get_vector_store(collection_name)
    return store.as_retriever(search_kwargs={"k": k})


def format_docs(docs):
    return "\n\n".join(f"[{d.metadata.get('source', '?')}] {d.page_content}" for d in docs)


def build_rag_chain(collection_name: str = "telecom_pdfs", k: int = 4):
    retriever = get_retriever(collection_name, k)
    llm = LLMFactory.get_llm(temperature=0.0, max_tokens=512)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )
    return chain


def query_troubleshooting(question: str, collection_name: str = "telecom_pdfs", k: int = 4) -> str:
    chain = build_rag_chain(collection_name, k)
    return chain.invoke(question)
