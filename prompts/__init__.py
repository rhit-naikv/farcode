from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent

# Cache for system prompt to avoid repeated file I/O
_system_prompt_cache = None


def load_prompt(name: str) -> str:
    """Load a prompt file from the prompts directory.

    Args:
        name: Name of the prompt file (without .md extension)

    Returns:
        The prompt content as a string

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    prompt_path = _PROMPTS_DIR / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")


def load_system_prompt() -> str:
    """Load the main system prompt for the coding agent (cached after first load)."""
    global _system_prompt_cache

    if _system_prompt_cache is None:
        _system_prompt_cache = load_prompt("system_prompt")

    return _system_prompt_cache


# Export the main loader
__all__ = ["load_system_prompt", "load_prompt"]
