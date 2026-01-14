import os
import shlex
import subprocess
from pathlib import Path
from time import time
from typing import List, Optional, Set

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import Field

# Maximum output length to prevent information disclosure
MAX_OUTPUT_LENGTH = 10000

# Shell operators that could be used for command injection
SHELL_OPERATORS: Set[str] = {
    ";",
    "&&",
    "||",
    "|",
    ">",
    ">>",
    "<",
    "<<",
    "&",
    "`",
    "$(",
    ")",
}


class SecureShellTool(BaseTool):
    """
    A secure shell tool that implements safeguards to prevent dangerous command execution.

    Security features:
    - Command whitelist/blacklist enforcement
    - Path validation with symlink resolution
    - Shell injection prevention (no shell operators, shell=False)
    - Execution timeout
    - Output truncation
    """

    name: str = "SecureShellTool"
    description: str = "Execute shell commands with security safeguards in place"
    allowed_commands: List[str] = Field(default_factory=list)
    forbidden_commands: List[str] = Field(default_factory=list)
    allowed_paths: List[str] = Field(default_factory=lambda: [os.getcwd()])
    timeout: int = Field(default=30)  # seconds

    def __init__(
        self,
        allowed_commands: Optional[List[str]] = None,
        forbidden_commands: Optional[List[str]] = None,
        allowed_paths: Optional[List[str]] = None,
        timeout: int = 30,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # Default safe commands that are typically needed for development tasks
        default_allowed_commands = [
            "ls",
            "pwd",
            "echo",
            "cat",
            "head",
            "tail",
            "grep",
            "find",
            "wc",
            "sort",
            "uniq",
            "cut",
            "date",
            "whoami",
            "hostname",
            "ps",
            "top",
            "df",
            "du",
            "free",
            "uname",
            "which",
            "whereis",
            "git",
            "python",
            "pip",
            "conda",
            "node",
            "npm",
            "yarn",
            "docker",
            "kubectl",
            "aws",
            "gcloud",
            "curl",
            "wget",
            "netstat",
            "ifconfig",
            "ping",
        ]

        # Dangerous commands that should be forbidden
        default_forbidden_commands = [
            "rm",
            "mv",
            "cp",
            "chmod",
            "chown",
            "mkdir",
            "touch",
            "dd",
            "mkfs",
            "mount",
            "umount",
            "losetup",
            "sudo",
            "su",
            "passwd",
            "usermod",
            "userdel",
            "groupadd",
            "groupdel",
            "shutdown",
            "halt",
            "reboot",
            "poweroff",
            "kill",
            "killall",
            "rmmod",
            "insmod",
            "modprobe",
            "shred",
            "sfdisk",
            "fdisk",
            "parted",
            "crontab",
            "at",
            "anacron",
            "chattr",
            "lsof",
            "nslookup",
            "dig",
            "traceroute",
            "tcpdump",
            "iptables",
            "firewall-cmd",
            "ufw",
        ]

        self.allowed_commands = allowed_commands or default_allowed_commands
        self.forbidden_commands = forbidden_commands or default_forbidden_commands
        self.allowed_paths = allowed_paths or [os.getcwd()]
        self.timeout = timeout

    def _contains_shell_operators(self, command: str) -> bool:
        """
        Check if command contains shell operators that could enable injection.

        Args:
            command: The raw command string to check

        Returns:
            bool: True if shell operators are found, False otherwise
        """
        for operator in SHELL_OPERATORS:
            if operator in command:
                return True
        return False

    def _run(
        self, command: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Execute a shell command with security checks.

        Args:
            command: The shell command to execute
            run_manager: Optional callback manager for tool runs

        Returns:
            str: The output of the command or an error message
        """
        # Initialize to satisfy static analysis - will be set during parsing
        parsed_command: List[str] = []

        try:
            # Check for shell operators before parsing
            if self._contains_shell_operators(command):
                return (
                    "Error: Command contains shell operators (;, &&, ||, |, >, <, etc.) "
                    "which are not allowed for security reasons. Please run commands separately."
                )

            # Parse the command to extract arguments
            try:
                parsed_command = shlex.split(command.strip())
            except ValueError as e:
                return f"Error: Invalid command syntax - {str(e)}"

            if not parsed_command:
                return "Error: Empty command provided"

            main_cmd = parsed_command[0]

            # Check if command is forbidden
            if main_cmd in self.forbidden_commands:
                return f"Error: Command '{main_cmd}' is forbidden for security reasons."

            # Check if command is allowed
            if main_cmd not in self.allowed_commands:
                return (
                    f"Error: Command '{main_cmd}' is not in the allowed list. "
                    f"Allowed commands: {', '.join(sorted(self.allowed_commands))}"
                )

            # Validate file paths in the command arguments
            path_error = self._validate_file_paths(parsed_command[1:])
            if path_error:
                return path_error

            # Execute the command with shell=False for security
            start_time = time()
            result = subprocess.run(
                parsed_command,  # Pass as list, not string
                shell=False,  # Prevent shell injection
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.getcwd(),
            )

            execution_time = time() - start_time

            # Build output
            if result.returncode == 0:
                output = result.stdout
            else:
                output = (
                    f"Command failed with return code {result.returncode}\n"
                    f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
                )

            # Limit output length to prevent information disclosure
            if len(output) > MAX_OUTPUT_LENGTH:
                output = (
                    f"{output[:MAX_OUTPUT_LENGTH]}\n... [output truncated for security]"
                )

            return output

        except subprocess.TimeoutExpired:
            return f"Error: Command exceeded timeout of {self.timeout} seconds"
        except FileNotFoundError:
            # parsed_command is guaranteed to be defined here since FileNotFoundError
            # can only occur during subprocess.run, which happens after parsing
            cmd_name = parsed_command[0] if parsed_command else "unknown"
            return f"Error: Command '{cmd_name}' not found"
        except PermissionError:
            return "Error: Permission denied to execute command"
        except OSError as e:
            return f"Error: OS error while executing command - {str(e)}"

    def _validate_file_paths(self, args: List[str]) -> Optional[str]:
        """
        Validate that command arguments don't reference paths outside allowed directories.

        Resolves symlinks to prevent symlink-based path traversal attacks.

        Args:
            args: List of command arguments to validate

        Returns:
            Optional[str]: Error message if validation fails, None if all paths are valid
        """
        for arg in args:
            # Skip flags (arguments starting with -)
            if arg.startswith("-"):
                continue

            # Skip if argument doesn't look like a path
            if not (
                arg.startswith("/")
                or arg.startswith("../")
                or arg.startswith("./")
                or "/" in arg
            ):
                continue

            try:
                # Resolve the path including symlinks
                path_obj = Path(arg)

                # For existing paths, resolve fully (follows symlinks)
                if path_obj.exists():
                    resolved_path = path_obj.resolve(strict=True)
                else:
                    # For non-existing paths, resolve the parent and append the name
                    # This prevents attacks using non-existent paths
                    parent = path_obj.parent
                    if parent.exists():
                        resolved_path = parent.resolve(strict=True) / path_obj.name
                    else:
                        # Parent doesn't exist, resolve what we can
                        resolved_path = path_obj.resolve(strict=False)

                # Check if the resolved path is within any of the allowed directories
                is_valid = False
                for allowed_path in self.allowed_paths:
                    allowed_resolved = Path(allowed_path).resolve()
                    try:
                        resolved_path.relative_to(allowed_resolved)
                        is_valid = True
                        break
                    except ValueError:
                        continue

                if not is_valid:
                    return (
                        f"Error: Path '{arg}' resolves to '{resolved_path}' which is "
                        f"outside allowed directories. Allowed paths: {', '.join(self.allowed_paths)}"
                    )
            except (OSError, RuntimeError) as e:
                # If we can't resolve the path, reject it for security
                return f"Error: Cannot validate path '{arg}' - {str(e)}"

        return None


def create_secure_shell_tool(**kwargs) -> SecureShellTool:
    """
    Factory function to create a SecureShellTool with default security settings.

    Args:
        **kwargs: Additional arguments to pass to SecureShellTool constructor

    Returns:
        SecureShellTool: A configured instance of SecureShellTool
    """
    return SecureShellTool(**kwargs)
