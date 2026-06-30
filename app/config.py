import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class LLMConfig:
    provider = os.getenv("LLM_PROVIDER", "openai")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini-2026-03-17")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
    openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_site_url = os.getenv("OPENROUTER_SITE_URL", "")
    openrouter_site_name = os.getenv("OPENROUTER_SITE_NAME", "Telecom Ticket Analyzer")

class S3Config:
    endpoint_url = os.getenv("S3_ENDPOINT_URL", "")
    access_key = os.getenv("S3_ACCESS_KEY", "")
    secret_key = os.getenv("S3_SECRET_KEY", "")
    bucket_name = os.getenv("S3_BUCKET_NAME", "telecom-pdfs")
    region = os.getenv("S3_REGION", "us-east-1")

class EmbeddingsConfig:
    provider = os.getenv("EMBEDDINGS_PROVIDER", "local")
    openrouter_model = os.getenv("OPENROUTER_EMBEDDINGS_MODEL", "text-embedding-3-small")

class AppConfig:
    chroma_db_path = Path(os.getenv("CHROMA_DB_PATH", str(PROJECT_ROOT / "data" / "chroma_db")))
    data_dir = PROJECT_ROOT / "data"
    synthetic_dir = data_dir / "synthetic"
    pdfs_dir = data_dir / "pdfs"
    db_path = Path(os.getenv("ANALYSES_DB_PATH", str(data_dir / "analyses.db")))
    ticket_count = 200
