# Farcode

A command-line chat application that leverages LangChain and the Groq API to interact with AI models.

## Overview

Farcode is a terminal-based chat interface that allows you to interact with AI models like Llama 3.3 70b. It supports both single-prompt execution and interactive chat sessions with conversation history.

## Features

- Interactive chat mode with conversation history
- Single-prompt execution for quick queries
- Session-based message storage
- Built with LangChain and Groq API

## Prerequisites

- Python 3.8+
- Groq API key (stored in environment variables)

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
   Create a `.env` file in the project root with your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
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

## Dependencies

- `langchain`: Framework for developing LLM applications
- `langchain-groq`: Integration with Groq API
- `langchain-community`: Community maintained LangChain integrations
- `typer`: Library for building command-line interfaces
- `python-dotenv`: Loads environment variables from `.env` file
- `rich`: For rich text and beautiful formatting in the terminal

## Architecture

The application uses:
- LangChain for LLM orchestration
- Groq API with the Llama-3.3-70b-versatile model
- In-memory session storage for conversation history
- Typer for command-line interface
