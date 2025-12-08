from pathlib import Path
from typing import Union


class PathResolver:
    """
    Utility class to securely resolve file paths relative to a base directory.
    Ensures that all file operations are constrained to the base directory to prevent
    directory traversal attacks.
    """

    def __init__(self, base_dir: Union[str, Path, None] = None):
        """
        Initialize the PathResolver with a base directory.

        Args:
            base_dir: Base directory for file operations. If None, uses current working directory.
        """
        if base_dir is None:
            base_dir = Path.cwd()
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir.resolve()

    def resolve_path(self, path: Union[str, Path]) -> Path:
        """
        Resolve a relative path to an absolute path within the base directory.

        Args:
            path: Relative path to resolve

        Returns:
            Absolute Path object within the base directory

        Raises:
            ValueError: If the resolved path is outside the base directory (security violation)
        """
        # Convert to Path object and resolve to absolute path
        requested_path = (self.base_dir / path).resolve()

        # Check if the resolved path is within the base directory
        try:
            # This will raise ValueError if the path is outside the base directory
            requested_path.relative_to(self.base_dir)
        except ValueError:
            raise ValueError(
                f"Path '{requested_path}' is outside the allowed base directory '{self.base_dir}'"
            )

        return requested_path

    def validate_and_resolve_path(self, path: Union[str, Path]) -> str:
        """
        Validate and resolve a path, returning the absolute string path.

        Args:
            path: Path to validate and resolve

        Returns:
            Absolute path as a string
        """
        absolute_path = self.resolve_path(path)
        return str(absolute_path)


def get_path_resolver(base_dir: Union[str, Path, None] = None) -> PathResolver:
    """
    Helper function to create a PathResolver instance.

    Args:
        base_dir: Base directory for the resolver. If None, uses current working directory.

    Returns:
        PathResolver instance
    """
    return PathResolver(base_dir)
