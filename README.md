# Farcode

A command-line chat application that leverages LangChain and AI models to interact with the system and perform various tasks including file operations and web searches.

## Overview

Farcode is a terminal-based chat interface that allows you to interact with AI models. It supports both single-prompt execution and interactive chat sessions with conversation history. The application includes secure file tools and web search capabilities.

## Features

- Interactive chat mode with conversation history
- Single-prompt execution for quick queries
- Secure file operations (read, write, list directories)
- Web search capabilities
- Session-based message storage
- Built with LangChain and AI models

## Prerequisites

- Python 3.8+
- API key for the selected model (stored in environment variables)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/farcode.git
   cd farcode
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with your API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

## Usage

### Interactive Mode
Run without any arguments to start an interactive chat session:
```bash
python main.py
```

### Single Prompt
Provide a single prompt as an argument:
```bash
python main.py "What is the weather today?"
```

## Available Tools

The application provides several tools for the AI agent to use:

- **File Operations**: Read, write, and list files within the current working directory
- **Web Search**: DuckDuckGo search integration for current information
- **AI Model**: Currently configured with openai/gpt-oss-120b model

## Dependencies

- `langchain`: Framework for developing LLM applications
- `langchain-groq`: Integration with AI model APIs
- `langchain-community`: Community maintained LangChain integrations
- `typer`: Library for building command-line interfaces
- `python-dotenv`: Loads environment variables from `.env` file
- `rich`: For rich text and beautiful formatting in the terminal

## Architecture

The application uses:
- LangChain for LLM orchestration
- Custom secure file tools for system interaction
- DuckDuckGo search integration for web queries
- In-memory session storage for conversation history
- Typer for command-line interface
- Configured with openai/gpt-oss-120b model with temperature 0.3
- Recursive tool calling with a limit of 15 calls
- Error handling for tool calling, API issues, and throttling
