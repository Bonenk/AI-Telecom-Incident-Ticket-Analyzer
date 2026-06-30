from typing import ClassVar
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from app.config import LLMConfig


class LLMFactory:
    _instances: ClassVar[dict[str, BaseChatModel]] = {}

    @classmethod
    def get_llm(cls, temperature: float = 0.1, max_tokens: int | None = 1024) -> BaseChatModel:
        cfg = LLMConfig()
        key = f"{cfg.provider}_{temperature}_{max_tokens}"
        if key in cls._instances:
            return cls._instances[key]

        llm = cls._build(cfg, temperature, max_tokens)
        cls._instances[key] = llm
        return llm

    @classmethod
    def _build(cls, cfg: LLMConfig, temperature: float, max_tokens: int | None) -> BaseChatModel:
        match cfg.provider:
            case "openai":
                return ChatOpenAI(
                    model=cfg.openai_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=cfg.openai_api_key,
                )
            case "anthropic":
                return ChatAnthropic(
                    model=cfg.anthropic_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=cfg.anthropic_api_key,
                )
            case "ollama":
                return ChatOllama(
                    model=cfg.ollama_model,
                    temperature=temperature,
                    num_predict=max_tokens,
                    base_url=cfg.ollama_base_url,
                )
            case "openrouter":
                headers = {}
                if cfg.openrouter_site_url:
                    headers["HTTP-Referer"] = cfg.openrouter_site_url
                if cfg.openrouter_site_name:
                    headers["X-Title"] = cfg.openrouter_site_name
                return ChatOpenAI(
                    model=cfg.openrouter_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=cfg.openrouter_api_key,
                    base_url=cfg.openrouter_base_url,
                    default_headers=headers,
                )
            case _:
                raise ValueError(f"Unsupported LLM provider: {cfg.provider}")
