import os

from langchain_groq import ChatGroq


def get_groq_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    return ChatGroq(model="openai/gpt-oss-120b", temperature=0.3)
