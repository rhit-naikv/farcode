import asyncio
import sys
from typing import Optional

import typer
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from rich.console import Console
from rich.text import Text

from callbacks import LoadingAndApprovalCallbackHandler
from commands import CommandHandler
from config import PROVIDERS, AgentState
from prompts import load_system_prompt
from providers.get_provider import get_llm_provider
from tools import get_tools

# HTTP error codes
HTTP_BAD_REQUEST: int = 400
HTTP_TOO_MANY_REQUESTS: int = 429

load_dotenv()

app = typer.Typer()
console = Console()


async def initialize_agent(provider: str = "open_router", model: Optional[str] = None):
    # Initialize the LLM
    llm = get_llm_provider(provider, model)

    # Create the full list of tools
    tools = await get_tools()

    # Define the system message for the agent
    system_prompt = load_system_prompt()

    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)


# Initialize command handler
command_handler = CommandHandler(console)


def is_waiting_for_selection(handler) -> bool:
    """Check if command handler is waiting for provider or model selection."""
    return handler.waiting_for_provider_selection or handler.waiting_for_model_selection


@app.command()
def main() -> None:
    asyncio.run(async_main())


async def async_main() -> None:
    """Interactive CLI for the Senior AI Software Engineer agent."""
    # Use Rich's Text class to safely handle static content with styles
    console.print(
        Text("Welcome to the Senior AI Software Engineer Agent!", style="bold green")
    )

    # Use Rich's Text class to safely handle static content with styles
    console.print(
        Text("Type 'exit' or 'quit' to stop the conversation.\n", style="yellow")
    )

    # Show help hint
    console.print(Text("Type '/help' to see available commands.\n", style="cyan"))

    # Initialize message history
    messages = []

    # Initialize approved tools set to be shared across requests in this session
    approved_tools = set()

    # Initialize the agent
    agent = await initialize_agent()

    # Initialize shared state for commands
    shared_state = AgentState(
        messages=messages,
        approved_tools=approved_tools,
        current_provider="open_router",
        current_model="xiaomi/mimo-v2-flash:free",
        agent=agent,
        model_changed=False,
    )

    while True:
        # Get the appropriate prompt based on command handler state
        prompt_text = command_handler.get_prompt()
        user_input = typer.prompt(prompt_text)

        # Check for empty input
        if not user_input.strip():
            continue

        # Check if we're in the middle of a multi-step command
        if is_waiting_for_selection(command_handler):
            # Process the input as part of the ongoing command
            command_executed, updated_state, should_exit = command_handler.execute(
                user_input, shared_state.__dict__
            )

            if command_executed:
                # Update shared state
                for key, value in updated_state.items():
                    if hasattr(shared_state, key):
                        setattr(shared_state, key, value)

                # Check if we should exit
                if should_exit:
                    break

                # Check if model was changed and agent needs to be recreated
                if shared_state.model_changed:
                    try:
                        # Get the new LLM
                        provider = shared_state.current_provider
                        model = shared_state.current_model
                        shared_state.agent = await initialize_agent(provider, model)

                        # Reset the flag
                        shared_state.model_changed = False

                        console.print(
                            Text(
                                f"\n✓ Agent successfully updated with "
                                f"{PROVIDERS[provider]['name']}/{model}",
                                style="bold green",
                            )
                        )

                    except Exception as e:
                        console.print(
                            Text(
                                f"\n✗ Failed to update agent: {str(e)}",
                                style="bold red",
                            )
                        )
                        console.print(
                            Text("Keeping the previous configuration.", style="yellow")
                        )

            continue
        # Check if it's a command (including exit/quit commands)
        elif command_handler.is_command(user_input):
            command_executed, updated_state, should_exit = command_handler.execute(
                user_input, shared_state.__dict__
            )

            if command_executed:
                # Update shared state
                for key, value in updated_state.items():
                    if hasattr(shared_state, key):
                        setattr(shared_state, key, value)

                # Check if we should exit
                if should_exit:
                    break

                # Check if model was changed and agent needs to be recreated
                if shared_state.model_changed:
                    try:
                        # Get the new LLM
                        provider = shared_state.current_provider
                        model = shared_state.current_model
                        shared_state.agent = await initialize_agent(provider, model)

                        # Reset the flag
                        shared_state.model_changed = False

                        console.print(
                            Text(
                                f"\n✓ Agent successfully updated with "
                                f"{PROVIDERS[provider]['name']}/{model}",
                                style="bold green",
                            )
                        )

                    except Exception as e:
                        console.print(
                            Text(
                                f"\n✗ Failed to update agent: {str(e)}",
                                style="bold red",
                            )
                        )
                        console.print(
                            Text("Keeping the previous configuration.", style="yellow")
                        )

            continue

        # Handle regular prompts (non-commands)
        # Check for exit/quit without slash
        if user_input.lower() in ["exit", "quit"]:
            console.print(Text("\nGoodbye!", style="bold green"))
            break

        try:
            # Add user message to history
            messages.append(HumanMessage(content=user_input))

            # Create a new callback handler for each request
            callback_handler = LoadingAndApprovalCallbackHandler(
                shared_approved_tools=approved_tools
            )

            # Start loading indicator since we're about to start processing
            callback_handler.start_loading("Processing your request...")

            # Track if we've started printing AI response
            has_started_printing_response = False
            full_response = ""

            # Get current agent from shared state
            current_agent = shared_state.agent

            # Stream with messages mode for token-by-token streaming
            async for event in current_agent.astream(
                {"messages": messages},
                config={"callbacks": [callback_handler]},
                stream_mode="messages",
            ):
                # event is a tuple of (message, metadata)
                message, metadata = event

                # Check if this is an AI message chunk with content
                if isinstance(message, (AIMessageChunk, AIMessage)):
                    # Handle content being either string or list
                    content = message.content
                    if isinstance(content, str) and content:
                        if not has_started_printing_response:
                            # Stop the loading indicator when we start getting actual content
                            # This should only happen once, when we first start printing
                            if (
                                callback_handler.live_display
                                and callback_handler.live_display.is_started
                            ):
                                callback_handler.stop_loading()

                            # Use Rich's Text class to safely handle static content
                            # with styles
                            response_header = Text()
                            response_header.append("\nResponse: ", style="blue")
                            console.print(response_header, end="")
                            has_started_printing_response = True

                        # Print the content token by token
                        # Disable markup parsing to prevent errors from
                        # AI-generated Rich markup
                        console.print(content, end="", style="blue", markup=False)
                        full_response += content

                        # Force flush to ensure immediate display
                        sys.stdout.flush()

            # Stop any remaining loading indicators
            callback_handler.stop_loading()

            # Print newline after streaming completes
            if has_started_printing_response:
                console.print()

            # Update message history with the AI response
            if full_response:
                messages.append(AIMessage(content=full_response))

        except Exception as e:
            error_msg = str(e)
            # Disable markup parsing to prevent errors from AI-generated Rich
            # markup in error messages
            # Use Rich's Text class to safely handle static content with styles
            console.print(Text(f"\nError: {error_msg}", style="red"))

            # Provide helpful error messages
            if "tool_use_failed" in error_msg:
                # Use Rich's Text class to safely handle static content with styles
                console.print(
                    Text("\nℹ️  Tool calling error detected...", style="yellow")
                )
            elif str(HTTP_BAD_REQUEST) in error_msg:
                # Use Rich's Text class to safely handle static content with styles
                console.print(Text("\nℹ️  API error...", style="yellow"))
            elif (
                str(HTTP_TOO_MANY_REQUESTS) in error_msg
                or "Too Many Requests" in error_msg
            ):
                # Use Rich's Text class to safely handle static content with styles
                console.print(Text("\nℹ️ throttling error...", style="yellow"))
            elif "was denied by user" in error_msg:
                # Use Rich's Text class to safely handle static content with styles
                console.print(
                    Text("\n⚠️  Tool call was denied by user.", style="yellow")
                )
            elif "Stopping execution" in error_msg:
                # Use Rich's Text class to safely handle static content with styles
                console.print(
                    Text("\n⚠️  Tool call was denied by user.", style="yellow")
                )

            # Remove the last user message on error
            if messages and isinstance(messages[-1], HumanMessage):
                messages.pop()

        console.print()


if __name__ == "__main__":
    app()
