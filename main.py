import typer
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_groq import ChatGroq
from rich.console import Console

from callbacks import LoadingAndApprovalCallbackHandler
from tools import getTools

load_dotenv()

app = typer.Typer()
console = Console()

# Initialize the LLM
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.3)

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
    console.print(
        "Welcome to the Senior AI Software Engineer Agent!", style="bold green"
    )
    console.print("Type 'exit' or 'quit' to stop the conversation.\n", style="yellow")

    # Initialize message history
    messages = []

    # Initialize approved tools set to be shared across requests in this session
    approved_tools = set()

    while True:
        user_input = typer.prompt("Enter your query")

        if user_input.lower() in ["exit", "quit"]:
            console.print("Goodbye!", style="bold green")
            break

        try:
            # Add user message to history
            messages.append(HumanMessage(content=user_input))

            # Show initial processing message
            console.print("[green]Processing your request...[/green]")

            # Create a new callback handler for each request to avoid state issues
            # but pass the shared approved tools to maintain approval across requests
            callback_handler = LoadingAndApprovalCallbackHandler(
                shared_approved_tools=approved_tools
            )

            # Invoke the agent with the messages and callback handler
            response = agent.invoke(
                {"messages": messages},
                config={"recursion_limit": 15, "callbacks": [callback_handler]},
            )

            # Stop any remaining loading indicators from the callback handler
            callback_handler.stop_loading()

            # Show completion message
            console.print("[green]Processing completed.[/green]")

            # Add the agent's response to the message history
            response_messages = response.get("messages", [])
            messages = response_messages

            # Find the last AI message to display
            ai_response = None
            for msg in reversed(response_messages):
                if isinstance(msg, AIMessage) and msg.content:
                    ai_response = msg.content
                    break

            if ai_response:
                console.print(f"Response: {ai_response}", style="blue")
            else:
                console.print("\nNo response content generated.", style="yellow")

        except Exception as e:
            error_msg = str(e)
            console.print(f"\nError: {error_msg}", style="red")

            # Provide helpful error messages
            if "tool_use_failed" in error_msg:
                console.print("\nℹ️  Tool calling error detected...", style="yellow")
            elif "400" in error_msg:
                console.print("\nℹ️  API error...", style="yellow")
            elif "429" in error_msg or "Too Many Requests" in error_msg:
                console.print("\nℹ️ Groq throttling error...", style="yellow")
            elif "was denied by user" in error_msg:
                console.print("\n⚠️  Tool call was denied by user.", style="yellow")
            elif "Stopping execution" in error_msg:
                console.print("\n⚠️  Tool call was denied by user.", style="yellow")

            # Remove the last user message on error
            if messages and isinstance(messages[-1], HumanMessage):
                messages.pop()

        console.print()


if __name__ == "__main__":
    app()
