import sys

import typer
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from rich.console import Console
from rich.text import Text

from callbacks import LoadingAndApprovalCallbackHandler
from providers.get_provider import get_llm_provider
from tools import getTools

load_dotenv()

app = typer.Typer()
console = Console()

# Initialize the LLM
llm = get_llm_provider("open_router")

# Create the full list of tools
tools = getTools()

# Define the system message for the agent
system_message = """You are an expert Senior AI Software Engineer. You must use the available tools to complete complex coding tasks, write files, read documentation, and search the web. You have access to read files, write files, list directories, and search the web. Use these tools as needed to help the user with their software engineering tasks. All file operations are restricted to the current working directory and its subdirectories.
IMPORTANT: When calling tools, you must return valid JSON responses in the proper OpenAI function calling format."""

# Create the agent using the new LangChain approach
agent = create_agent(model=llm, tools=tools, system_prompt=system_message)


@app.command()
def main():
    """Interactive CLI for the Senior AI Software Engineer agent."""
    # Use Rich's Text class to safely handle static content with styles
    welcome_text = Text()
    welcome_text.append(
        "Welcome to the Senior AI Software Engineer Agent!", style="bold green"
    )
    console.print(welcome_text)

    # Use Rich's Text class to safely handle static content with styles
    exit_text = Text()
    exit_text.append(
        "Type 'exit' or 'quit' to stop the conversation.\n", style="yellow"
    )
    console.print(exit_text)

    # Initialize message history
    messages = []

    # Initialize approved tools set to be shared across requests in this session
    approved_tools = set()

    while True:
        user_input = typer.prompt("Enter your query")

        if user_input.lower() in ["exit", "quit"]:
            # Use Rich's Text class to safely handle static content with styles
            goodbye_text = Text()
            goodbye_text.append("Goodbye!", style="bold green")
            console.print(goodbye_text)
            break

        try:
            # Add user message to history
            messages.append(HumanMessage(content=user_input))

            # Create a new callback handler for each request
            callback_handler = LoadingAndApprovalCallbackHandler(
                shared_approved_tools=approved_tools
            )

            # Track if we've started printing AI response
            has_started_printing_response = False
            full_response = ""

            # Stream with messages mode for token-by-token streaming
            # Wrap messages in a dict with "messages" key for the agent state
            for event in agent.stream(
                {"messages": messages},
                config={"callbacks": [callback_handler]},
                stream_mode="messages",
            ):
                # Stop the loading indicator when we start getting actual content
                # During streaming, we show the response as it arrives rather than using loading indicators
                if (
                    callback_handler.live_display
                    and callback_handler.live_display.is_started
                ):
                    callback_handler.stop_loading()

                # event is a tuple of (message, metadata)
                message, metadata = event

                # Check if this is an AI message chunk with content
                if isinstance(message, (AIMessageChunk, AIMessage)):
                    # Handle content being either string or list
                    content = message.content
                    if isinstance(content, str) and content:
                        if not has_started_printing_response:
                            # Use Rich's Text class to safely handle static content with styles
                            response_header = Text()
                            response_header.append("\nResponse: ", style="blue")
                            console.print(response_header, end="")
                            has_started_printing_response = True

                        # Print the content token by token
                        # Disable markup parsing to prevent errors from AI-generated Rich markup
                        console.print(content, end="", style="blue", markup=False)
                        full_response += content

                        # Force flush to ensure immediate display
                        sys.stdout.flush()

            # Stop any remaining loading indicators
            callback_handler.stop_loading()

            # Print newline after streaming completes
            if has_started_printing_response:
                console.print()

            # Use Rich's Text class to safely handle static content with styles
            processing_text = Text()
            processing_text.append("Processing completed.", style="green")
            console.print(processing_text)

            # Update message history with the AI response
            if full_response:
                messages.append(AIMessage(content=full_response))

        except Exception as e:
            error_msg = str(e)
            # Disable markup parsing to prevent errors from AI-generated Rich markup in error messages
            # Use Rich's Text class to safely handle static content with styles
            error_text = Text()
            error_text.append(f"\nError: {error_msg}", style="red")
            console.print(error_text)

            # Provide helpful error messages
            if "tool_use_failed" in error_msg:
                # Use Rich's Text class to safely handle static content with styles
                error_help_text = Text()
                error_help_text.append(
                    "\nℹ️  Tool calling error detected...", style="yellow"
                )
                console.print(error_help_text)
            elif "400" in error_msg:
                # Use Rich's Text class to safely handle static content with styles
                error_help_text = Text()
                error_help_text.append("\nℹ️  API error...", style="yellow")
                console.print(error_help_text)
            elif "429" in error_msg or "Too Many Requests" in error_msg:
                # Use Rich's Text class to safely handle static content with styles
                error_help_text = Text()
                error_help_text.append("\nℹ️ throttling error...", style="yellow")
                console.print(error_help_text)
            elif "was denied by user" in error_msg:
                # Use Rich's Text class to safely handle static content with styles
                error_help_text = Text()
                error_help_text.append(
                    "\n⚠️  Tool call was denied by user.", style="yellow"
                )
                console.print(error_help_text)
            elif "Stopping execution" in error_msg:
                # Use Rich's Text class to safely handle static content with styles
                error_help_text = Text()
                error_help_text.append(
                    "\n⚠️  Tool call was denied by user.", style="yellow"
                )
                console.print(error_help_text)

            # Remove the last user message on error
            if messages and isinstance(messages[-1], HumanMessage):
                messages.pop()

        console.print()


if __name__ == "__main__":
    app()
