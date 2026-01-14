# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Farcode is a Python CLI agentic coding assistant built on LangChain. It provides an interactive REPL-style chat interface with streaming responses, tool calling with user approval, and multi-provider LLM support.

## Commands

```bash
# Run the application
python main.py

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

No test suite or linting configuration exists currently.

## Architecture

```
main.py                  # Entry point, async REPL, agent orchestration
config.py                # PROVIDERS dict, TOOL_NAMES, AgentState dataclass
callbacks/               # LangChain callback handlers for UI and tool approval
commands/                # CLI commands (/help, /model, /status, /clear, /tools, /exit)
providers/               # LLM provider factories (OpenRouter, Google, Groq)
tools/                   # Tool implementations
  ├── get_tools.py       # Tool aggregation
  ├── secure_shell_tool.py  # Whitelist/blacklist shell execution
  └── mcp.py             # Model Context Protocol integration
prompts/
  └── system_prompt.md   # Comprehensive agentic AI instructions
```

### Core Flow
1. User input → CommandHandler checks for `/` commands
2. Chat messages → HumanMessage → LangChain agent with tool calling
3. Tool calls require user approval (approve-once-for-session available)
4. Streaming responses via async astream

### Key Patterns
- **Async/await** throughout - agent initialization and message streaming are async
- **Factory pattern** in `providers/get_provider.py` for LLM instantiation
- **Callback handlers** manage loading indicators, tool approval UI, and status messages
- **AgentState dataclass** tracks messages, approved tools, current provider/model

## Configuration

- API keys: `.env` file (GROQ_API_KEY, GOOGLE_API_KEY, OPEN_ROUTER_API_KEY)
- MCP servers: `~/.farcode/settings.json` with `mcpServers` array
- Python version: 3.13.11 (`.python-version`)

## Security Constraints

The SecureShellTool (`tools/secure_shell_tool.py`) enforces:
- **Whitelist**: ~40 safe commands (ls, git, python, npm, docker, etc.)
- **Blacklist**: ~40 dangerous commands (rm, chmod, sudo, shutdown, etc.)
- **Path restriction**: Operations limited to current working directory
- **Timeout**: 30 seconds
- **Output truncation**: 10,000 characters

File operations are restricted to CWD and subdirectories.

## Supported Providers

Defined in `config.py`:
- **OpenRouter**: xiaomi/mimo-v2-flash, mistralai/devstral-2512, x-ai/grok-code-fast-1
- **Google**: gemini-2.5-flash
- **Groq**: openai/gpt-oss-120b

Switch via `/model` command during runtime.

## Context7 MCP Usage

**Proactively use Context7 MCP** (via `resolve-library-id` and `query-docs` tools) without explicit requests when:

1. **Answering library/API questions** about project dependencies (LangChain, LangGraph, Typer, Rich, Pydantic, python-dotenv, DuckDuckGo Search)
2. **Implementing features** requiring library setup, configuration, or integration patterns
3. **Generating code** that relies on external libraries (LangChain agents, LangGraph workflows, callback handlers, tool definitions, etc.)
4. **Determining best practices** for using a library in this project's context
5. **Debugging library-specific issues** (agent execution errors, tool calling failures, provider integration issues, MCP adapter problems)

**Do NOT use Context7 for:**
- Project-specific patterns (use CLAUDE.md instead)
- Internal architecture questions (check codebase structure)
- Features fully documented in project files
- General software engineering (only library-specific guidance)
