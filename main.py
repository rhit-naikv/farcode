import asyncio
import sys
from typing import Optional, Tuple

import typer
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from rich.console import Console
from rich.text import Text

from callbacks import LoadingAndApprovalCallbackHandler
from commands import CommandHandler
from config import DEFAULT_MODEL, DEFAULT_PROVIDER, PROVIDERS, AgentState
from prompts import load_system_prompt
from providers.get_provider import get_llm_provider
from tools import get_tools

# HTTP error codes
HTTP_BAD_REQUEST: int = 400
HTTP_TOO_MANY_REQUESTS: int = 429

load_dotenv()

app = typer.Typer()
console = Console()


async def initialize_agent(
    provider: str = DEFAULT_PROVIDER, model: Optional[str] = None
):
    """
    Initialize the LangChain agent with the specified provider and model.

    Args:
        provider: LLM provider key from config.PROVIDERS
        model: Model identifier, or None to use provider's default

    Returns:
        Configured LangChain agent instance
    """
    llm = get_llm_provider(provider, model)
    tools = await get_tools()
    system_prompt = load_system_prompt()
    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)


# Initialize command handler
command_handler = CommandHandler(console)


def is_waiting_for_selection(handler: CommandHandler) -> bool:
    """Check if command handler is waiting for provider or model selection."""
    return handler.waiting_for_provider_selection or handler.waiting_for_model_selection


async def handle_model_change(shared_state: AgentState) -> None:
    """
    Handle model change by reinitializing the agent.

    Updates shared_state.agent with a new agent instance configured
    for the current provider/model, and resets the model_changed flag.

    Args:
        shared_state: Current agent state to update
    """
    if not shared_state.model_changed:
        return

    try:
        provider = shared_state.current_provider
        model = shared_state.current_model
        shared_state.agent = await initialize_agent(provider, model)
        shared_state.model_changed = False

        console.print(
            Text(
                f"\n Agent successfully updated with "
                f"{PROVIDERS[provider]['name']}/{model}",
                style="bold green",
            )
        )
    except Exception as e:
        console.print(Text(f"\n Failed to update agent: {str(e)}", style="bold red"))
        console.print(Text("Keeping the previous configuration.", style="yellow"))


def process_command(user_input: str, shared_state: AgentState) -> Tuple[bool, bool]:
    """
    Process a command and update shared state.

    Args:
        user_input: The user's input string
        shared_state: Current agent state

    Returns:
        Tuple of (command_was_executed, should_exit)
    """
    command_executed, updated_state, should_exit = command_handler.execute(
        user_input, shared_state.__dict__
    )

    if command_executed:
        shared_state.update_from_dict(updated_state)

    return command_executed, should_exit


def handle_error(error_msg: str, messages: list) -> None:
    """
    Handle and display errors with context-appropriate messages.

    Args:
        error_msg: The error message string
        messages: Message history (last message removed if it was user's)
    """
    console.print(Text(f"\nError: {error_msg}", style="red"))

    # Provide helpful error messages
    if "tool_use_failed" in error_msg:
        console.print(Text("\n  Tool calling error detected...", style="yellow"))
    elif str(HTTP_BAD_REQUEST) in error_msg:
        console.print(Text("\n  API error...", style="yellow"))
    elif str(HTTP_TOO_MANY_REQUESTS) in error_msg or "Too Many Requests" in error_msg:
        console.print(Text("\n  Throttling error...", style="yellow"))
    elif "was denied by user" in error_msg or "Stopping execution" in error_msg:
        console.print(Text("\n  Tool call was denied by user.", style="yellow"))

    # Remove the last user message on error
    if messages and isinstance(messages[-1], HumanMessage):
        messages.pop()


@app.command()
def main() -> None:
    asyncio.run(async_main())


async def async_main() -> None:
    """Interactive CLI for the Senior AI Software Engineer agent."""
    console.print(
        Text("Welcome to the Senior AI Software Engineer Agent!", style="bold green")
    )
    console.print(
        Text("Type 'exit' or 'quit' to stop the conversation.\n", style="yellow")
    )
    console.print(Text("Type '/help' to see available commands.\n", style="cyan"))

    # Initialize the agent
    agent = await initialize_agent()

    # Initialize shared state for commands
    shared_state = AgentState(
        messages=[],
        approved_tools=set(),
        current_provider=DEFAULT_PROVIDER,
        current_model=DEFAULT_MODEL,
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

        # Process commands (either mid-selection or new command)
        if is_waiting_for_selection(command_handler) or command_handler.is_command(
            user_input
        ):
            command_executed, should_exit = process_command(user_input, shared_state)

            if command_executed:
                if should_exit:
                    break
                await handle_model_change(shared_state)

            continue

        # Handle regular prompts (non-commands)
        if user_input.lower() in ["exit", "quit"]:
            console.print(Text("\nGoodbye!", style="bold green"))
            break

        # Create a new callback handler for each request
        callback_handler = LoadingAndApprovalCallbackHandler(
            shared_approved_tools=shared_state.approved_tools
        )

        try:
            # Add user message to history
            shared_state.messages.append(HumanMessage(content=user_input))

            # Start loading indicator
            callback_handler.start_loading("Processing your request...")

            # Track streaming state
            has_started_printing_response = False
            full_response = ""

            # Stream with messages mode for token-by-token streaming
            async for event in shared_state.agent.astream(
                {"messages": shared_state.messages},
                config={"callbacks": [callback_handler]},
                stream_mode="messages",
            ):
                message, metadata = event

                if isinstance(message, (AIMessageChunk, AIMessage)):
                    content = message.content
                    if isinstance(content, str) and content:
                        if not has_started_printing_response:
                            if (
                                callback_handler.live_display
                                and callback_handler.live_display.is_started
                            ):
                                callback_handler.stop_loading()

                            response_header = Text()
                            response_header.append("\nResponse: ", style="blue")
                            console.print(response_header, end="")
                            has_started_printing_response = True

                        console.print(content, end="", style="blue", markup=False)
                        full_response += content
                        sys.stdout.flush()

            callback_handler.stop_loading()

            if has_started_printing_response:
                console.print()

            if full_response:
                shared_state.messages.append(AIMessage(content=full_response))

        except Exception as e:
            callback_handler.stop_loading()
            handle_error(str(e), shared_state.messages)

        console.print()


if __name__ == "__main__":
    app()
