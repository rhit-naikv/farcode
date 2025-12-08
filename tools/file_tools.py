from pathlib import Path

from langchain_core.tools import tool

from utils.path_resolver import get_path_resolver


@tool
def read_file(file_path: str) -> str:
    """Read a file from the current working directory. Only accessible within the directory where the agent is instantiated."""
    try:
        # Initialize the path resolver with the current working directory
        path_resolver = get_path_resolver(Path.cwd())
        # Resolve the path securely
        absolute_path = path_resolver.validate_and_resolve_path(file_path)
        path_obj = Path(absolute_path)

        # Verify it's a file
        if not path_obj.is_file():
            return f"Error: Path is not a file: {absolute_path}"

        # Read and return file content
        with open(path_obj, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file in the current working directory. Only accessible within the directory where the agent is instantiated."""
    try:
        # Initialize the path resolver with the current working directory
        path_resolver = get_path_resolver(Path.cwd())
        # Resolve the path securely
        absolute_path = path_resolver.validate_and_resolve_path(file_path)

        # Create parent directories if they don't exist
        Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(absolute_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def list_directory(dir_path: str = ".") -> str:
    """List the contents of a directory in the current working directory. Only accessible within the directory where the agent is instantiated."""
    try:
        # Initialize the path resolver with the current working directory
        path_resolver = get_path_resolver(Path.cwd())
        # Resolve the path securely
        absolute_path = path_resolver.validate_and_resolve_path(dir_path)
        path_obj = Path(absolute_path)

        if not path_obj.is_dir():
            return f"Error: Path is not a directory: {absolute_path}"

        files = []
        directories = []

        for item in path_obj.iterdir():
            if item.is_file():
                files.append(item.name)
            elif item.is_dir():
                directories.append(item.name)

        result = {"files": sorted(files), "directories": sorted(directories)}

        return str(result)
    except Exception as e:
        return f"Error listing directory: {str(e)}"
