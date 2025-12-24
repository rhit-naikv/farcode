from providers.google import get_google_llm
from providers.groq import get_groq_llm
from providers.open_router import get_open_router_llm


def get_llm_provider(provider_name: str):
    if provider_name.lower() == "google":
        return get_google_llm()
    elif provider_name.lower() == "groq":
        return get_groq_llm()
    elif provider_name.lower() == "open_router":
        return get_open_router_llm()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
