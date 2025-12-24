import os

from langchain_openai import ChatOpenAI
from pydantic import SecretStr


def get_open_router_llm():
    api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPEN_ROUTER_API_KEY environment variable is not set")

    return ChatOpenAI(
        model="mistralai/devstral-2512:free",
        api_key=SecretStr(api_key),
        base_url="https://openrouter.ai/api/v1",
    )
