# AI Telecom Incident Ticket Analyzer

An AI-powered ticket analysis system for telecom operations. Uses LangGraph agent workflows, RAG from technical PDFs, and a Streamlit UI.

## Features

- **Multi-agent workflow**: Classification → Severity → Resolution (with RAG from telecom PDFs) → Human Approval
- **Smart routing**: Auto-resolves low-severity billing tickets; routes complex tickets to full RAG resolution
- **RAG-powered**: Retrieves relevant troubleshooting steps from indexed telecom PDFs (ChromaDB)
- **Human-in-the-loop**: Approve, edit, reject, or **Keep Open** AI-generated resolutions
- **Multi-provider LLM**: OpenAI, Anthropic, Ollama, or OpenRouter
- **S3-compatible storage**: Cloudflare R2, AWS S3, or MinIO
- **Multi-page UI**: Dashboard, Ticket Analysis, Tickets, Knowledge Base, History
- **Light/Dark theme**: Toggle via sidebar selectbox
- **Actionable Tickets page**: Filter open/approved/rejected tickets; approve/edit/reject directly from the list
- **PDF Knowledge Base**: Browse, upload, and index PDFs; document registry tracks all uploaded files

## Quick Start

### Local (uv)

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and enter the project
git clone <repo-url> && cd telecom-ticket-analyzer

# Install dependencies
uv sync

# Copy and edit environment config
cp .env.example .env
# Edit .env with your API keys (see Environment Variables below)

# Generate synthetic data and seed the database
uv run python scripts/generate_data.py

# Start the app
uv run streamlit run app/streamlit_app.py
```

### Docker

```bash
# Build and run
docker compose up --build -d

# View logs
docker logs telecom-ticket-analyzer -f

# Stop
docker compose down
```

The app is available at `http://localhost:8501`.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | No | `openai` | `openai`, `anthropic`, `ollama`, or `openrouter` |
| `OPENAI_API_KEY` | Yes* | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-5.4-mini-2026-03-17` | OpenAI model name |
| `ANTHROPIC_API_KEY` | Yes* | — | Anthropic API key |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-20250514` | Anthropic model name |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | No | `llama3.2` | Ollama model name |
| `OPENROUTER_API_KEY` | Yes* | — | OpenRouter API key |
| `OPENROUTER_MODEL` | No | `openai/gpt-4o` | OpenRouter model name |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | OpenRouter base URL |
| `OPENROUTER_SITE_URL` | No | — | Site URL sent with OpenRouter requests |
| `OPENROUTER_SITE_NAME` | No | `Telecom Ticket Analyzer` | Site name sent with OpenRouter requests |
| `EMBEDDINGS_PROVIDER` | No | `local` | `openai`, `openrouter`, or `local` (HuggingFace) |
| `OPENROUTER_EMBEDDINGS_MODEL` | No | `text-embedding-3-small` | Embeddings model via OpenRouter |
| `S3_ENDPOINT_URL` | Yes* | — | S3-compatible endpoint URL |
| `S3_ACCESS_KEY` | Yes* | — | S3 access key |
| `S3_SECRET_KEY` | Yes* | — | S3 secret key |
| `S3_BUCKET_NAME` | No | `telecom-pdfs` | S3 bucket name |
| `S3_REGION` | No | `us-east-1` | S3 region |
| `CHROMA_DB_PATH` | No | `data/chroma_db` | ChromaDB persistence path |
| `ANALYSES_DB_PATH` | No | `data/analyses.db` | SQLite analyses database path |

\* Required depending on chosen provider. See `.env.example` for a commented template.

## Project Structure

```
├── app/
│   ├── agents/              # LangGraph agent nodes (classification, severity, resolution, human approval)
│   ├── components/          # Streamlit UI components (agent cards, ticket selector, approval panel, styles)
│   ├── data/                # PDF generator, synthetic data generator
│   ├── pages/               # Streamlit pages (dashboard, ticket analysis, tickets, knowledge base, history)
│   ├── rag/                 # RAG pipeline (vector store, retriever, document loader)
│   ├── services/            # Core services (LLM factory, database, S3, summarizer)
│   ├── utils/               # Helpers
│   ├── workflow/            # LangGraph workflow orchestrator
│   ├── config.py            # Central configuration (reads from .env)
│   └── streamlit_app.py     # App entry point (5-page navigation)
├── data/
│   ├── analyses.db          # SQLite database (ticket analyses, synthetic tickets, outage logs, PDF registry)
│   ├── chroma_db/           # ChromaDB vector store persistence
│   ├── pdfs/                # Generated & uploaded troubleshooting PDFs
│   └── synthetic/           # Generated test data
├── scripts/
│   ├── generate_data.py     # Synthetic data generator + PDF generation via LLM
│   ├── index_pdfs.py        # Index PDFs into ChromaDB
│   ├── upload_to_s3.py      # Upload PDFs to S3-compatible storage
│   └── deploy.sh            # EC2 deployment script (Docker or direct)
├── tests/                   # 52 unit tests (agents, workflow, RAG, services, database)
├── .dockerignore
├── .env.example             # Environment template with all options
├── docker-compose.yml       # Docker Compose for local dev / Coolify / EC2
├── Dockerfile               # Multi-stage production build
├── pyproject.toml           # Project metadata and dependencies
├── requirements.txt         # Pinned dependency list
└── uv.lock                  # uv lock file
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## Deployment

### Docker (Coolify or AWS EC2)

The same `Dockerfile` and `docker-compose.yml` work on both platforms.

```bash
# Build and run
docker compose up --build -d

# The app listens on 0.0.0.0:8501
# Persistent data is stored in ./data/ (mounted at /app/data)
```

#### Coolify

1. Add a new **Docker Compose** resource
2. Point it to your repository
3. Set environment variables in Coolify's UI (or use a `.env` file)
4. Add a persistent volume mount for `/app/data`
5. Deploy — Coolify handles HTTPS, reverse proxy, and port mapping

#### EC2 (automated)

```bash
# Docker-based (default)
./scripts/deploy.sh --user ubuntu --host <EC2_IP> --key ~/.ssh/key.pem [--domain example.com]

# Direct systemd + uv (original)
./scripts/deploy.sh --user ubuntu --host <EC2_IP> --key ~/.ssh/key.pem --direct
```

### Manual (no Docker)

```bash
uv sync
cp .env.example .env
# Edit .env with your API keys
uv run streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

## Architecture

1. User submits a ticket (from dataset or custom input with auto-generated ID)
2. **Classification Agent** determines category (Network, Billing, Hardware, Software, Customer)
3. **Severity Agent** assesses impact (Critical/High/Medium/Low) with a score
4. **Router** decides: auto-resolve (low-severity billing) or full resolution with RAG
5. **Resolution Agent** queries ChromaDB (indexed from telecom PDFs) for relevant troubleshooting context, then generates a resolution
6. **Human Approval** panel allows Approve / Edit / Reject / Keep Open before finalizing
7. Results are saved to SQLite (`ticket_analyses`) and displayed on the Dashboard, Tickets page, and History page

### Pages

| Page | Description |
|---|---|
| **Dashboard** | Stats (analyzed, pending, critical, resolved), recent tickets with expandable details, "View all tickets" link |
| **Ticket Analysis** | Full workflow: ticket selector → agent cards (live streaming) → resolution display → human approval → download |
| **Tickets** | Filterable list (status, severity, category) of all analyzed tickets; inline approve/edit/reject for open tickets |
| **Knowledge Base** | Browse indexed PDFs, upload & index new PDFs, document registry |
| **History** | Three tabs: Analyzed Tickets (from DB), Synthetic Dataset, Outage Logs |
