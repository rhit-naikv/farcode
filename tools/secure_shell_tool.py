import os
import shlex
import subprocess
from pathlib import Path
from time import time
from typing import List, Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import Field

# Maximum output length to prevent information disclosure
MAX_OUTPUT_LENGTH = 10000


class SecureShellTool(BaseTool):
    """
    A secure version of the shell tool that implements various safeguards to prevent
    dangerous command execution.
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
        try:
            # Parse the command to extract the main command
            parsed_command = shlex.split(command.strip())
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
                    f"Allowed commands: {', '.join(self.allowed_commands)}"
                )

            # Validate file paths in the command to ensure they are within
            # allowed paths
            if not self._validate_file_paths(parsed_command[1:]):
                return (
                    f"Error: Command references paths outside of allowed directories. "
                    f"Allowed paths: {', '.join(self.allowed_paths)}"
                )

            # Execute the command with a timeout
            start_time = time()
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.getcwd(),  # Restrict execution to current working directory
            )

            execution_time = time() - start_time

            # Check if command timed out
            if execution_time >= self.timeout:
                return f"Error: Command exceeded timeout of {self.timeout} seconds"

            # Return stdout and stderr
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
        except Exception as e:
            return f"Error: Failed to execute command - {str(e)}"

    def _validate_file_paths(self, args: List[str]) -> bool:
        """
        Check if any of the command arguments reference paths outside of allowed paths.

        Args:
            args: List of command arguments to validate

        Returns:
            bool: True if all paths are within allowed paths, False otherwise
        """
        for arg in args:
            # Skip if argument doesn't look like a path
            if not (
                arg.startswith("/")
                or arg.startswith("../")
                or arg.startswith("./")
                or "/" in arg
            ):
                continue

            try:
                # Resolve the path and check if it's within allowed paths
                path_obj = Path(arg).resolve()

                # Check if the resolved path is within any of the allowed directories
                is_valid = any(
                    str(path_obj).startswith(str(Path(allowed_path).resolve()))
                    for allowed_path in self.allowed_paths
                )

                if not is_valid:
                    return False
            except Exception:
                # If we can't resolve the path, consider it invalid for security
                return False

        return True


def create_secure_shell_tool(**kwargs) -> SecureShellTool:
    """
    Factory function to create a SecureShellTool with default security settings.

    Args:
        **kwargs: Additional arguments to pass to SecureShellTool constructor

    Returns:
        SecureShellTool: A configured instance of SecureShellTool
    """
    return SecureShellTool(**kwargs)
