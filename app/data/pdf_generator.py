import json
import re
import hashlib
from pathlib import Path
from fpdf import FPDF

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.services.llm_service import LLMFactory

PDF_TOPIC_TITLES = [
    "5G NR Troubleshooting Guide",
    "5G SA Core Network Troubleshooting",
    "LTE eNB Troubleshooting Guide",
    "Microwave Link Alignment and Troubleshooting",
    "GPON Network Troubleshooting",
    "XGS-PON Installation and Troubleshooting",
    "DWDM Network Fault Isolation",
    "Fiber Optic Network Repair Manual",
    "VOIP Quality and Troubleshooting Handbook",
    "SIP Trunking Troubleshooting",
    "Network Security and Firewall Configuration",
    "Billing System Error Resolution Guide",
    "Mobile App and API Troubleshooting",
    "CPE and Home Router Configuration Guide",
    "Small Cell Deployment and Troubleshooting",
    "MIMO and Beamforming Optimization",
    "SD-WAN Troubleshooting Guide",
    "IoT Device Connectivity Troubleshooting",
    "Network Monitoring and NMS Configuration",
    "Customer SLA and Escalation Management",
]

GENERATION_PROMPT = """You are a senior telecom engineer creating a detailed troubleshooting guide for field technicians.

Generate realistic, technically accurate content for a PDF troubleshooting guide titled:

  "{title}"

The content MUST follow this exact JSON structure — no markdown, no code fences, no extra text:

{{
  "title": "{title}",
  "sections": [
    ["Overview", "2-3 sentence introduction describing what this guide covers."],
    ["Step 1: ...", "Detailed step with CLI commands, expected output, specific thresholds, and troubleshooting actions."],
    ["Step 2: ...", "Next procedure with technical details, measurements, and decision criteria."],
    ["Step 3: ...", "Additional step with configuration snippets, diagnostic commands, and resolution actions."],
    ["Common Issues and Fixes", "3-5 bullet points with specific issues and their fixes using the format: Issue: description Fix: action"],
    ["Tools and Commands Reference", "List of CLI commands, tools, and their purpose relevant to this guide."],
    ["Escalation Criteria", "When to escalate to Tier 3: specific thresholds, error patterns, and conditions."]
  ]
}}

Guidelines:
- Use realistic CLI commands, configuration snippets, and technical thresholds with specific numerical values (dBm, ms, Mbps, GHz, etc.)
- Each section body must be 100-250 words of dense technical content
- Lines starting with "  - " or "- " will render as bullet points
- Lines starting with "|" with pipes will render as table rows
- Use backtick-wrapped text like `command` for CLI commands and code references
- Use \\n for line breaks within section content
- Covers topics from a major telecom service provider perspective
- Include specific error codes, model numbers, and real-world scenarios"""


def _sanitize(text: str) -> str:
    replacements = {
        "\u2014": "--", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2022": "-", "\u2026": "...",
        "\u00b1": "+/-", "\u00b0": " deg", "\u2264": "<=", "\u2265": ">=",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _generate_content(title: str) -> dict | None:
    llm = LLMFactory.get_llm(temperature=0.7, max_tokens=3072)
    chain = ChatPromptTemplate.from_messages([
        ("system", "You are a telecom PDF content generator. Output ONLY valid JSON with the exact structure requested. Do not include markdown code fences or any text outside the JSON object."),
        ("human", GENERATION_PROMPT),
    ]) | llm | StrOutputParser()

    raw = chain.invoke({"title": title})
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        if "title" not in data or "sections" not in data:
            return None
        if not isinstance(data["sections"], list) or len(data["sections"]) < 3:
            return None
        data["sections"] = [(s[0], s[1]) for s in data["sections"] if isinstance(s, list) and len(s) >= 2]
        if not data["sections"]:
            return None
        return data
    except (json.JSONDecodeError, KeyError, IndexError):
        return None


def _cache_path(output_dir: Path, title: str) -> Path:
    cache_dir = output_dir / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    h = hashlib.md5(title.encode()).hexdigest()[:12]
    return cache_dir / f"{h}.json"


def get_topic_content(title: str, output_dir: Path, force: bool = False) -> dict | None:
    cache = _cache_path(output_dir, title)
    if not force and cache.exists():
        try:
            with open(cache) as f:
                return json.load(f)
        except Exception:
            pass

    data = _generate_content(title)
    if data:
        with open(cache, "w") as f:
            json.dump(data, f)
    return data


def create_pdf(topic: dict, output_path: Path):
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, _sanitize(topic["title"]), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    for section_title, section_body in topic["sections"]:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, _sanitize(section_title), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 10)
        for line in section_body.split("\n"):
            line = line.strip()
            if not line:
                pdf.ln(2)
                continue
            line = _sanitize(line)
            if line.startswith("|"):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                col_width = 180 // max(len(parts), 1)
                for p in parts:
                    pdf.cell(col_width, 7, p, border=1)
                pdf.ln()
                pdf.set_x(pdf.l_margin)
            elif line.startswith("  - ") or line.startswith("- "):
                pdf.set_x(pdf.l_margin + 10)
                pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 10, 6, line)
                pdf.set_x(pdf.l_margin)
            else:
                pdf.multi_cell(0, 6, line)
                pdf.set_x(pdf.l_margin)
        pdf.ln(3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))


def generate_pdfs(output_dir: Path, force: bool = False) -> list[str]:
    titles = []
    for i, title in enumerate(PDF_TOPIC_TITLES, 1):
        filename = f"{i:02d}_{title.replace(' ', '_').replace(':', '').replace('.', '').replace('&', 'and')}.pdf"
        pdf_path = output_dir / filename

        if not force and pdf_path.exists():
            titles.append(title)
            print(f"  SKIP {title} (exists)")
            continue

        print(f"  Generating: {title}...")
        content = get_topic_content(title, output_dir, force=force)
        if not content:
            print(f"  FAIL {title} — content generation failed, skipping.")
            continue

        create_pdf(content, pdf_path)
        print(f"    -> {pdf_path.name}")
        titles.append(title)

    return titles
