import json
import re
from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.services.llm_service import LLMFactory
from app.rag.retriever import get_retriever, format_docs

RESOLUTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a senior telecom engineer. Based on the ticket details and the troubleshooting "
        "context from technical guides, suggest a specific resolution.\n\n"
        "Consider:\n"
        "  1. The ticket category and severity\n"
        "  2. Relevant troubleshooting steps from the context\n"
        "  3. Industry best practices\n\n"
        'Respond with ONLY raw JSON (no markdown, no code fences):\n'
        '{{\n'
        '  "resolution": "<step-by-step resolution>",\n'
        '  "estimated_time": "<e.g., 30 minutes, 2 hours>",\n'
        '  "references": ["<source doc names>"]\n'
        "}}",
    ),
    ("human", "Category: {category}\nSeverity: {severity}\nSubject: {subject}\nDescription: {description}\n\nTroubleshooting context:\n{context}"),
])


def _parse_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "resolution": "Investigate the issue based on ticket details. Check relevant troubleshooting guides.",
            "estimated_time": "TBD",
            "references": [],
        }


def suggest_resolution(ticket: dict, category: str, severity: str, collection: str = "telecom_pdfs") -> dict:
    retriever = get_retriever(collection, k=3)
    llm = LLMFactory.get_llm(temperature=0.1, max_tokens=512)

    chain = (
        {
            "context": itemgetter("subject") | retriever | format_docs,
            "category": itemgetter("category"),
            "severity": itemgetter("severity"),
            "subject": itemgetter("subject"),
            "description": itemgetter("description"),
        }
        | RESOLUTION_PROMPT
        | llm
        | StrOutputParser()
    )

    raw = chain.invoke({
        "subject": ticket.get("subject", ""),
        "description": ticket.get("description", ""),
        "category": category,
        "severity": severity,
    })
    return _parse_json(raw)
