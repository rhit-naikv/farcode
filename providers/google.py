import os

from langchain_google_genai import ChatGoogleGenerativeAI


def get_google_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash")
