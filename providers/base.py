"""Base provider class for LLM providers."""

import os
from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.language_models import BaseChatModel


class BaseProvider(ABC):
    """
    Abstract base class for LLM providers.

    Provides common functionality for API key validation and model defaults.
    Subclasses must implement _create_llm() to return the specific LLM instance.
    """

    # Subclasses must define these
    env_var_name: str = ""
    default_model: str = ""
    provider_name: str = ""

    @classmethod
    def get_api_key(cls) -> str:
        """
        Get the API key from environment variables.

        Returns:
            The API key string

        Raises:
            ValueError: If the environment variable is not set
        """
        api_key = os.getenv(cls.env_var_name)
        if not api_key:
            raise ValueError(
                f"{cls.env_var_name} environment variable is not set. "
                f"Please set it in your .env file or environment."
            )
        return api_key

    @classmethod
    @abstractmethod
    def _create_llm(cls, model: str, api_key: str) -> BaseChatModel:
        """
        Create the LLM instance.

        Args:
            model: The model identifier to use
            api_key: The API key for authentication

        Returns:
            Configured BaseChatModel instance
        """
        pass

    @classmethod
    def get_llm(cls, model: Optional[str] = None) -> BaseChatModel:
        """
        Get a configured LLM instance.

        Args:
            model: Optional model name (uses default if not provided)

        Returns:
            Configured BaseChatModel instance
        """
        api_key = cls.get_api_key()
        model_name = model or cls.default_model
        return cls._create_llm(model_name, api_key)
