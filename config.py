"""Configuration for the Farcode CLI application."""

from dataclasses import dataclass
from typing import Any, Dict, List

# Available providers and their models
PROVIDERS: Dict[str, Dict[str, Any]] = {
    "open_router": {
        "name": "OpenRouter",
        "models": [
            "xiaomi/mimo-v2-flash:free",
            "mistralai/devstral-2512:free",
        ],
    },
    "google": {
        "name": "Google",
        "models": [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
    },
    "groq": {
        "name": "Groq",
        "models": [
            "openai/gpt-oss-120b",
        ],
    },
}

# Available tool names (for display purposes)
TOOL_NAMES: List[str] = [
    "ListDirectoryTool",
    "ReadFileTool",
    "WriteFileTool",
    "CopyFileTool",
    "MoveFileTool",
    "DeleteFileTool",
    "FileSearchTool",
    "DuckDuckGoSearchRun",
    "SecureShellTool",
]


@dataclass
class AgentState:
    """State management for the AI agent."""

    messages: List[Any]
    approved_tools: set
    current_provider: str
    current_model: str
    agent: Any
    model_changed: bool = False
