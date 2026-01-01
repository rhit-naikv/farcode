"""Get LLM provider with optional model override."""

from typing import Optional

from langchain_core.language_models import BaseChatModel

from providers.google import get_google_llm
from providers.groq import get_groq_llm
from providers.open_router import get_open_router_llm


def get_llm_provider(provider_name: str, model: Optional[str] = None) -> BaseChatModel:
    """
    Get an LLM instance for the specified provider.

    Args:
        provider_name: Name of the provider (google, groq, open_router)
        model: Optional model name to override the default

    Returns:
        Configured LLM instance
    """
    if provider_name.lower() == "google":
        return get_google_llm(model=model)
    elif provider_name.lower() == "groq":
        return get_groq_llm(model=model)
    elif provider_name.lower() == "open_router":
        return get_open_router_llm(model=model)
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
