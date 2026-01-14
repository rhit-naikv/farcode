"""Configuration for the Farcode CLI application."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# Type alias for message types used in conversations
MessageType = Union[HumanMessage, AIMessage, SystemMessage]

# Available providers and their models
PROVIDERS: Dict[str, Dict[str, Any]] = {
    "open_router": {
        "name": "OpenRouter",
        "models": [
            "xiaomi/mimo-v2-flash:free",
            "mistralai/devstral-2512:free",
            "x-ai/grok-code-fast-1",
        ],
    },
    "google": {
        "name": "Google",
        "models": [
            "gemini-2.5-flash",
        ],
    },
    "groq": {
        "name": "Groq",
        "models": [
            "openai/gpt-oss-120b",
        ],
    },
}

# Default provider and model
DEFAULT_PROVIDER = "open_router"
DEFAULT_MODEL = PROVIDERS[DEFAULT_PROVIDER]["models"][0]

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
    """
    State management for the AI agent.

    Attributes:
        messages: Conversation history as LangChain message objects
        approved_tools: Set of tool names approved for this session
        current_provider: Active LLM provider key (e.g., 'open_router', 'google')
        current_model: Active model identifier within the provider
        agent: The LangChain agent instance (Any due to various agent types)
        model_changed: Flag indicating if model was changed and agent needs reinitialization
    """

    messages: List[MessageType] = field(default_factory=list)
    approved_tools: Set[str] = field(default_factory=set)
    current_provider: str = DEFAULT_PROVIDER
    current_model: str = DEFAULT_MODEL
    agent: Optional[Any] = None  # Agent type varies based on implementation
    model_changed: bool = False

    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """
        Safely update state from a dictionary.

        Only updates known attributes to prevent accidental state corruption.

        Args:
            updates: Dictionary of attribute names to new values
        """
        allowed_attrs = {
            "messages",
            "approved_tools",
            "current_provider",
            "current_model",
            "agent",
            "model_changed",
        }
        for key, value in updates.items():
            if key in allowed_attrs and hasattr(self, key):
                setattr(self, key, value)
