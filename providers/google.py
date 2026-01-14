"""Google Gemini LLM provider."""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from providers.base import BaseProvider


class GoogleProvider(BaseProvider):
    """Google Gemini LLM provider."""

    env_var_name = "GOOGLE_API_KEY"
    default_model = "gemini-2.5-flash"
    provider_name = "Google"

    @classmethod
    def _create_llm(cls, model: str, api_key: str) -> BaseChatModel:
        return ChatGoogleGenerativeAI(model=model)


def get_google_llm(model: Optional[str] = None) -> BaseChatModel:
    """
    Get Google Gemini LLM instance.

    Args:
        model: Optional model name (defaults to gemini-2.5-flash)

    Returns:
        Configured ChatGoogleGenerativeAI instance
    """
    return GoogleProvider.get_llm(model)
