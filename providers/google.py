import os
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI


def get_google_llm(model: Optional[str] = None) -> BaseChatModel:
    """
    Get Google Gemini LLM instance.

    Args:
        model: Optional model name (defaults to gemini-2.0-flash)

    Returns:
        Configured ChatGoogleGenerativeAI instance
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")

    # Use provided model or default
    model_name = model or "gemini-2.0-flash"

    return ChatGoogleGenerativeAI(model=model_name)
