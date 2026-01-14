"""OpenRouter LLM provider."""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):
    """OpenRouter LLM provider for accessing multiple models."""

    env_var_name = "OPEN_ROUTER_API_KEY"
    default_model = "xiaomi/mimo-v2-flash:free"
    provider_name = "OpenRouter"

    @classmethod
    def _create_llm(cls, model: str, api_key: str) -> BaseChatModel:
        return ChatOpenAI(
            model=model,
            api_key=SecretStr(api_key),
            base_url="https://openrouter.ai/api/v1",
        )


def get_open_router_llm(model: Optional[str] = None) -> BaseChatModel:
    """
    Get OpenRouter LLM instance.

    Args:
        model: Optional model name (defaults to xiaomi/mimo-v2-flash:free)

    Returns:
        Configured ChatOpenAI instance
    """
    return OpenRouterProvider.get_llm(model)
