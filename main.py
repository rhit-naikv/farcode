import os

import typer
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import AIMessage, HumanMessage
from langchain_groq import ChatGroq
from rich.console import Console

# Import our custom secure tools
from tools.file_tools import (
    list_directory,
    read_file,
    write_file,
)

load_dotenv()

app = typer.Typer()
console = Console()

# Initialize the LLM
llm = ChatGroq(model="llama-3.3-70b-versatile")

# Initialize our secure tools
read_file_tool = read_file
write_file_tool = write_file
list_directory_tool = list_directory

# Initialize the search tool
search_tool = DuckDuckGoSearchRun()

# Create the full list of tools
tools = [read_file_tool, write_file_tool, list_directory_tool, search_tool]

# Define the system message for the agent
system_message = "You are an expert Senior AI Software Engineer. You must use the available tools to complete complex coding tasks, write files, read documentation, and search the web. You have access to read files, write files, list directories, and search the web. Use these tools as needed to help the user with their software engineering tasks. All file operations are restricted to the current working directory and its subdirectories."

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

    while True:
        user_input = typer.prompt("Enter your query")

        if user_input.lower() in ["exit", "quit"]:
            console.print("Goodbye!", style="bold green")
            break

        try:
            # Add user message to history
            messages.append(HumanMessage(content=user_input))

            # Invoke the agent with the messages
            response = agent.invoke({"messages": messages})

            # Add the agent's response to the message history
            ai_response = response["messages"][-1].content
            messages.append(AIMessage(content=ai_response))

            console.print(f"Response: {ai_response}", style="blue")
        except Exception as e:
            console.print(f"Error: {str(e)}", style="red")

        console.print()


if __name__ == "__main__":
    app()
