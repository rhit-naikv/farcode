"""Command handler for the AI agent CLI."""

from typing import List, Optional, Tuple

from rich.console import Console
from rich.text import Text

from config import PROVIDERS, TOOL_NAMES


class CommandHandler:
    """Handles all CLI commands for the agent."""

    def __init__(self, console: Console):
        self.console = console
        self.commands = {
            "help": self.show_help,
            "model": self.change_model,
            "providers": self.list_providers,
            "status": self.show_status,
            "clear": self.clear_history,
            "tools": self.list_tools,
            "quit": self.quit_agent,
            "exit": self.quit_agent,
        }
        # State for multi-step commands
        self.waiting_for_provider_selection = False
        self.waiting_for_model_selection = False
        self.selected_provider = None

    def is_command(self, input_text: str) -> bool:
        """Check if input is a command."""
        return input_text.strip().startswith("/")

    def execute(self, input_text: str, current_state: dict) -> Tuple[bool, dict, bool]:
        """
        Execute a command.

        Returns:
            Tuple of (command_executed, updated_state, should_exit)
        """
        # Handle multi-step model selection
        if self.waiting_for_provider_selection:
            # Expect a number input for provider selection
            stripped_input = input_text.strip()
            if stripped_input.isdigit():
                provider_num = int(stripped_input)
                provider_keys = list(PROVIDERS.keys())
                if 1 <= provider_num <= len(provider_keys):
                    selected_provider_key = provider_keys[provider_num - 1]
                    provider_info = PROVIDERS[selected_provider_key]
                    self.console.print(
                        f"\n[bold green]Selected provider: {provider_info['name']} ({selected_provider_key})[/bold green]"
                    )

                    # Now wait for model selection
                    self.selected_provider = selected_provider_key
                    self.waiting_for_provider_selection = False
                    self.waiting_for_model_selection = True

                    # Show available models for this provider
                    self._show_models_for_provider(provider_info)
                    return True, current_state, False
                else:
                    self._print_error(
                        f"Invalid provider number. Please enter a number between 1 and {len(provider_keys)}"
                    )
                    return True, current_state, False
            else:
                self._print_error("Please enter a number corresponding to the provider")
                return True, current_state, False

        elif self.waiting_for_model_selection and self.selected_provider:
            # Expect a number input for model selection
            stripped_input = input_text.strip()
            if stripped_input.isdigit():
                model_num = int(stripped_input)
                provider_info = PROVIDERS[self.selected_provider]
                models = provider_info["models"]

                if 1 <= model_num <= len(models):
                    selected_model = models[model_num - 1]

                    # Update state with new provider and model
                    updated_state = current_state.copy()
                    updated_state["current_provider"] = self.selected_provider
                    updated_state["current_model"] = selected_model
                    updated_state["model_changed"] = True

                    self.console.print(
                        f"\n[bold green]✓ Model selected: {provider_info['name']}/{selected_model}[/bold green]"
                    )

                    # Reset multi-step state
                    self.waiting_for_provider_selection = False
                    self.waiting_for_model_selection = False
                    self.selected_provider = None

                    return True, updated_state, False
                else:
                    self._print_error(
                        f"Invalid model number. Please enter a number between 1 and {len(models)}"
                    )
                    return True, current_state, False
            else:
                self._print_error("Please enter a number corresponding to the model")
                return True, current_state, False

        # Handle regular commands
        if not self.is_command(input_text):
            return False, current_state, False

        parts = input_text.strip().split()
        command_name = parts[0][1:].lower()  # Remove leading slash
        args = parts[1:]  # Get all arguments after command name

        if command_name in self.commands:
            try:
                # Pass current state and any arguments to the command
                result = self.commands[command_name](args, current_state)

                # Commands can return:
                # - None: no state change
                # - dict: updated state
                # - (dict, bool): updated state and exit flag
                if result is None:
                    return True, current_state, False
                elif isinstance(result, tuple):
                    return True, result[0], result[1]
                else:
                    return True, result, False
            except Exception as e:
                self._print_error(f"Command error: {str(e)}")
                return True, current_state, False
        else:
            self._print_error(f"Unknown command: /{command_name}")
            self._print_info("Use /help to see available commands")
            return True, current_state, False

    def show_help(self, args: List[str], state: dict) -> None:
        """Show available commands."""
        self.console.print("\n[bold cyan]Available Commands:[/bold cyan]")
        self.console.print("  [green]/help[/green] - Show this help message")
        self.console.print(
            "  [green]/model[/green] - Change AI model and provider (use /model for interactive selection, or /model <provider> <model_name>)"
        )
        self.console.print("  [green]/providers[/green] - List available providers")
        self.console.print("  [green]/tools[/green] - List available tools")
        self.console.print("  [green]/status[/green] - Show current configuration")
        self.console.print(
            "  [green]/exit[/green] or [green]/quit[/green] - Exit the agent"
        )

    def change_model(self, args: List[str], state: dict) -> Optional[dict]:
        """Change the AI model and provider. Usage: /model <provider> <model_name> or /model to see options."""
        if not args:
            # Start interactive model selection
            self.console.print("\n[bold cyan]Available Providers:[/bold cyan]")
            provider_list = list(PROVIDERS.keys())
            for i, provider_key in enumerate(provider_list, 1):
                provider_info = PROVIDERS[provider_key]
                self.console.print(f"  [{i}] {provider_info['name']} ({provider_key})")

            self.console.print(
                "\n[italic]Please enter the number of the provider you want to use:[/italic]"
            )
            self.waiting_for_provider_selection = True
            return None

        if len(args) < 2:
            self._print_error("Usage: /model <provider> <model_name>")
            self._print_info("Example: /model google gemini-2.0-flash")
            self._print_info(
                "Or use number from /model list: /model 1 gemini-2.0-flash"
            )
            return None

        # Check if the first argument is a number (referring to provider by index)
        provider_name = args[0].lower()
        if provider_name.isdigit():
            provider_index = int(provider_name) - 1
            provider_keys = list(PROVIDERS.keys())
            if 0 <= provider_index < len(provider_keys):
                provider_name = provider_keys[provider_index]
            else:
                self._print_error(
                    f"Invalid provider number: {args[0]}. Valid range: 1-{len(provider_keys)}"
                )
                return None
        else:
            # Validate provider name directly
            if provider_name not in PROVIDERS:
                self._print_error(f"Unknown provider: {provider_name}")
                self._print_info("Use /providers to see available providers")
                return None

        model_name = args[1]

        # Validate model
        provider_info = PROVIDERS[provider_name]
        if model_name not in provider_info["models"]:
            self._print_error(f"Unknown model: {model_name}")
            self._print_info(
                f"Available models for {provider_info['name']}: {', '.join(provider_info['models'])}"
            )
            return None

        # Update state with new provider and model
        updated_state = state.copy()
        updated_state["current_provider"] = provider_name
        updated_state["current_model"] = model_name
        updated_state["model_changed"] = True

        self.console.print(
            f"\n[bold green]✓ Model selected: {provider_info['name']}/{model_name}[/bold green]"
        )
        return updated_state

    def _show_models_for_provider(self, provider_info):
        """Show available models for a specific provider."""
        self.console.print(
            f"\n[bold cyan]Available Models for {provider_info['name']}:[/bold cyan]"
        )
        for i, model in enumerate(provider_info["models"], 1):
            self.console.print(f"  [{i}] {model}")
        self.console.print(
            "\n[italic]Please enter the number of the model you want to use:[/italic]"
        )

    def _show_model_selection_ui(self):
        """Show interactive UI for model selection."""
        self.console.print("\n[bold cyan]Available Providers:[/bold cyan]")
        provider_list = list(PROVIDERS.keys())
        for i, provider_key in enumerate(provider_list, 1):
            provider_info = PROVIDERS[provider_key]
            self.console.print(f"  [{i}] {provider_info['name']} ({provider_key})")
            # Show models for each provider
            for model in provider_info["models"]:
                self.console.print(f"      • {model}")

        self.console.print(
            "\n[italic]Usage: /model <provider> <model_name> or /model <number> <model_name>[/italic]"
        )
        self.console.print(
            "[italic]Examples: /model google gemini-2.0-flash or /model 1 gemini-2.0-flash[/italic]"
        )

    def get_prompt(self) -> str:
        """Get the appropriate prompt based on current command state."""
        if self.waiting_for_provider_selection:
            return "Enter provider number"
        elif self.waiting_for_model_selection:
            return "Enter model number"
        else:
            return "Enter your query"

    def list_providers(self, args: List[str], state: dict) -> None:
        """List all available providers and their models."""
        self.console.print("\n[bold cyan]Available Providers and Models:[/bold cyan]\n")

        for provider_key, provider_info in PROVIDERS.items():
            self.console.print(
                f"[bold green]{provider_info['name']} ({provider_key})[/bold green]"
            )
            for model in provider_info["models"]:
                self.console.print(f"  • {model}")
            self.console.print()

    def list_tools(self, args: List[str], state: dict) -> None:
        """List all available tools."""
        self.console.print("\n[bold cyan]Available Tools:[/bold cyan]\n")
        for tool in TOOL_NAMES:
            self.console.print(f"  • {tool}")
        self.console.print(
            "\n[italic]The agent can use these tools to help with your requests[/italic]"
        )

    def show_status(self, args: List[str], state: dict) -> None:
        """Show current configuration."""
        self.console.print("\n[bold cyan]Current Configuration:[/bold cyan]")

        provider = state.get("current_provider", "open_router")
        model = state.get("current_model", "xiaomi/mimo-v2-flash:free")

        self.console.print(
            f"  Provider: [green]{PROVIDERS.get(provider, {}).get('name', provider)}[/green]"
        )
        self.console.print(f"  Model: [green]{model}[/green]")
        self.console.print(
            f"  Conversation history: [green]{len(state.get('messages', []))} messages[/green]"
        )
        self.console.print(
            f"  Approved tools: [green]{len(state.get('approved_tools', set()))} tools[/green]"
        )

    def clear_history(self, args: List[str], state: dict) -> dict:
        """Clear conversation history."""
        updated_state = state.copy()
        updated_state["messages"] = []
        self.console.print("\n[bold green]✓ Conversation history cleared[/bold green]")
        return updated_state

    def quit_agent(self, args: List[str], state: dict) -> Tuple[dict, bool]:
        """Exit the agent."""
        self.console.print("\n[bold green]Goodbye![/bold green]")
        return (state, True)

    def _print_error(self, message: str) -> None:
        """
        Print an error message with red styling.

        Args:
            message: The error message to display
        """
        text = Text(f"\n✗ {message}", style="bold red")
        self.console.print(text)

    def _print_info(self, message: str) -> None:
        """
        Print an info message with yellow styling.

        Args:
            message: The info message to display
        """
        text = Text(f" {message}", style="yellow")
        self.console.print(text)
