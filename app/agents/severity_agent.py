import json
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.services.llm_service import LLMFactory

SEVERITY_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a telecom severity analyst. Assess the impact of this ticket.\n\n"
        "Severity levels:\n"
        "- Critical (score 81-100): Complete service outage, multiple customers/business affected, revenue impact\n"
        "- High (score 61-80): Partial outage, severe degradation, VIP customer, single business customer\n"
        "- Medium (score 41-60): Single residential customer affected, non-urgent degradation, billing issue\n"
        "- Low (score 1-40): Inquiry, informational, feature request, minor issue\n\n"
        'Respond with ONLY raw JSON (no markdown, no code fences):\n'
        '{{\n'
        '  "severity": "<Critical|High|Medium|Low>",\n'
        '  "score": <int 1-100>,\n'
        '  "reasoning": "<brief reason>"\n'
        "}}",
    ),
    ("human", "Category: {category}\nSubject: {subject}\nDescription: {description}"),
])


def _parse_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"severity": "Medium", "score": 50, "reasoning": "fallback - parse error"}


def detect_severity(ticket: dict, category: str) -> dict:
    llm = LLMFactory.get_llm(temperature=0.0, max_tokens=256)
    chain = SEVERITY_PROMPT | llm | StrOutputParser()
    raw = chain.invoke({
        "category": category,
        "subject": ticket.get("subject", ""),
        "description": ticket.get("description", ""),
    })
    return _parse_json(raw)
