import os
from typing import Optional

from langchain_openai import ChatOpenAI
from pydantic import SecretStr


def get_open_router_llm(model: Optional[str] = None):
    """
    Get OpenRouter LLM instance.

    Args:
        model: Optional model name (defaults to xiaomi/mimo-v2-flash:free)
    """
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPEN_ROUTER_API_KEY environment variable is not set")

    # Use provided model or default
    model_name = model or "xiaomi/mimo-v2-flash:free"

    return ChatOpenAI(
        model=model_name,
        api_key=SecretStr(api_key),
        base_url="https://openrouter.ai/api/v1",
    )
