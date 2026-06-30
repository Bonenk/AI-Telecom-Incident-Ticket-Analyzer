import json
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.services.llm_service import LLMFactory

CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a telecom ticket classifier. Analyze the ticket and classify it into exactly one category.\n\n"
        "Categories:\n"
        "- Network: Connectivity, latency, packet loss, outage, VOIP, DNS, BGP, fiber, 5G signal, VPN\n"
        "- Billing: Charges, invoices, payments, refunds, credits, plan changes, taxes\n"
        "- Hardware: Routers, ONTs, modems, switches, CPE, antennas, power supplies, ports\n"
        "- Software: CRM, API, provisioning, billing system, OSS, NMS, SMS gateway, mobile app\n"
        "- Customer: Service requests, complaints, escalations, appointment changes, account transfers\n\n"
        'Respond with ONLY raw JSON (no markdown, no code fences):\n'
        '{{\n'
        '  "category": "<category>",\n'
        '  "confidence": <0.0-1.0>,\n'
        '  "reasoning": "<brief reason>"\n'
        "}}",
    ),
    ("human", "Subject: {subject}\nDescription: {description}"),
])


def _parse_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"category": "Customer", "confidence": 0.5, "reasoning": "fallback - parse error"}


def classify_ticket(ticket: dict) -> dict:
    llm = LLMFactory.get_llm(temperature=0.0, max_tokens=256)
    chain = CLASSIFICATION_PROMPT | llm | StrOutputParser()
    raw = chain.invoke({
        "subject": ticket.get("subject", ""),
        "description": ticket.get("description", ""),
    })
    return _parse_json(raw)
