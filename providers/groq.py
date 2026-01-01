import os
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq


def get_groq_llm(model: Optional[str] = None) -> BaseChatModel:
    """
    Get Groq LLM instance.

    Args:
        model: Optional model name (defaults to openai/gpt-oss-120b)

    Returns:
        Configured ChatGroq instance
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")

    # Use provided model or default
    model_name = model or "openai/gpt-oss-120b"

    return ChatGroq(model=model_name, temperature=0.3)
