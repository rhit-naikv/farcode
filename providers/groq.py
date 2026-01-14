"""Groq LLM provider."""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq

from providers.base import BaseProvider


class GroqProvider(BaseProvider):
    """Groq LLM provider with fast inference."""

    env_var_name = "GROQ_API_KEY"
    default_model = "openai/gpt-oss-120b"
    provider_name = "Groq"

    @classmethod
    def _create_llm(cls, model: str, api_key: str) -> BaseChatModel:
        return ChatGroq(model=model, temperature=0.3)


def get_groq_llm(model: Optional[str] = None) -> BaseChatModel:
    """
    Get Groq LLM instance.

    Args:
        model: Optional model name (defaults to openai/gpt-oss-120b)

    Returns:
        Configured ChatGroq instance
    """
    return GroqProvider.get_llm(model)
