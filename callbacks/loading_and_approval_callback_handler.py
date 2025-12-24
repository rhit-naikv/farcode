import time

import typer
from langchain_core.callbacks import BaseCallbackHandler
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

console = Console()


class LoadingAndApprovalCallbackHandler(BaseCallbackHandler):
    """Custom callback handler to show loading indicators and approve tool calls"""

    def __init__(self, shared_approved_tools=None):
        # Use the shared approved tools set, or create a new one if not provided
        # Use 'is None' check instead of truthy check to properly handle empty set
        self.shared_approved_tools = (
            shared_approved_tools if shared_approved_tools is not None else set()
        )
        # We'll use rich's built-in spinner instead of custom threading
        self.spinner = Spinner("aesthetic")
        self.live_display = None

    def start_loading(self, message):
        """Start the loading indicator using Rich's Live display"""
        # Stop any existing live display
        if self.live_display and self.live_display.is_started:
            self.live_display.stop()

        # Create a custom renderable that updates the spinner with current time
        class SpinnerRenderable:
            def __init__(self, spinner, message):
                self.spinner = spinner
                self.message = message

            def __rich_console__(self, console, options):
                content = self.spinner.render(time.time())
                # Create the spinner text and message separately to avoid markup conflicts
                result = Text()
                result.append(content)  # Spinner content
                result.append(" ")  # Space
                result.append(self.message, style="green")  # Message with green style
                yield result

        # Create a new Live display with the spinner content
        spinner_renderable = SpinnerRenderable(self.spinner, message)
        self.live_display = Live(
            spinner_renderable, refresh_per_second=10, transient=True
        )
        self.live_display.start()

    def stop_loading(self):
        """Stop the loading indicator"""
        if self.live_display and self.live_display.is_started:
            self.live_display.stop()
            # Clear the display by outputting a blank line
            console.print(" ", end="\r")  # Clear the line

    def on_chain_start(self, serialized, inputs, **kwargs):
        """Called when the chain starts processing - but we'll skip UI updates for internal agent steps"""
        # Skip UI updates for internal agent steps to avoid duplicate messages
        # Only handle at tool level
        pass

    def on_chain_end(self, outputs, **kwargs):
        """Called when the chain finishes processing - but we'll skip UI updates for internal agent steps"""
        # Skip UI updates for internal agent steps to avoid duplicate messages
        # Only handle at tool level
        pass

    def on_tool_start(self, serialized, input_str, **kwargs):
        """Called when a tool starts"""
        self.stop_loading()

        # Extract tool name from serialized
        tool_name = (
            serialized.get("name", "Unknown Tool")
            if isinstance(serialized, dict)
            else "Unknown Tool"
        )
        tool_args = input_str if isinstance(input_str, str) else str(input_str)

        # Show tool call details and ask for approval
        console.print(
            Panel(
                f"[bold yellow]Tool Call:[/bold yellow] {tool_name}\n[bold cyan]Arguments:[/bold cyan] {tool_args}",
                border_style="yellow",
            )
        )

        # Ask user for approval if not already approved in this session
        if tool_name not in self.shared_approved_tools:
            approval = typer.prompt(
                f"Do you want to allow '{tool_name}'? (y/Y to approve, n/N to deny, a/A to approve for all future calls)",
                type=str,
                default="y",
            ).lower()

            if approval == "a":
                # Approve for all future calls in this session
                self.shared_approved_tools.add(tool_name)
                console.print(
                    f"[green]Approved '{tool_name}' for all future calls in this session.[/green]"
                )
            elif approval != "y":
                console.print(
                    f"[red]Denied '{tool_name}'. Skipping this tool call.[/red]"
                )
                # Instead of raising an exception, we'll return early to avoid the tool execution
                # Unfortunately, this approach doesn't work with LangChain's callback system
                # The only way to stop execution is to raise an exception
                raise RuntimeError(
                    f"Tool '{tool_name}' was denied by user. Stopping execution."
                )
        else:
            console.print(f"[green]Using previously approved tool: {tool_name}[/green]")

        # Show loading status for tool execution
        console.print(f"[green]Executing {tool_name}...[/green]")
        self.start_loading(f"Executing {tool_name}")

    def on_tool_end(self, output, **kwargs):
        """Called when a tool finishes"""
        self.stop_loading()
        console.print("[green]Tool execution completed.[/green]")
        self.start_loading("Processing")
