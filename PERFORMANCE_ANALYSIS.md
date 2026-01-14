# Performance Analysis Report

**Date:** 2026-01-14
**Codebase:** Farcode CLI Agent
**Analysis Type:** Performance Anti-patterns, N+1 Issues, Inefficient Algorithms

## Executive Summary

This analysis identified **11 performance issues** across the codebase, ranging from high-impact inefficiencies to minor optimizations. The most critical issues involve:
- Unnecessary tool re-initialization on model changes
- Repeated file I/O for static content
- Inefficient string concatenation in streaming loops
- Redundant path resolution operations

## Critical Issues (High Impact)

### 1. Tool Re-initialization on Agent Change
**File:** `main.py:29-45`
**Severity:** HIGH
**Type:** Unnecessary Re-computation

**Problem:**
```python
async def initialize_agent(
    provider: str = DEFAULT_PROVIDER, model: Optional[str] = None
):
    llm = get_llm_provider(provider, model)
    tools = await get_tools()  # ⚠️ Recreates all tools every time
    system_prompt = load_system_prompt()  # ⚠️ Reloads from disk every time
    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)
```

**Impact:**
- Called on every model change (line 73)
- Reinitializes 9+ tool instances that don't depend on the LLM
- Async MCP tool initialization happens unnecessarily
- Wasted CPU and I/O on every model switch

**Recommendation:**
```python
# Cache tools and system prompt at module level
_cached_tools = None
_cached_system_prompt = None

async def initialize_agent(provider: str = DEFAULT_PROVIDER, model: Optional[str] = None):
    global _cached_tools, _cached_system_prompt

    llm = get_llm_provider(provider, model)

    if _cached_tools is None:
        _cached_tools = await get_tools()
    if _cached_system_prompt is None:
        _cached_system_prompt = load_system_prompt()

    return create_agent(model=llm, tools=_cached_tools, system_prompt=_cached_system_prompt)
```

---

### 2. Inefficient String Concatenation in Streaming Loop
**File:** `main.py:202-230`
**Severity:** HIGH
**Type:** O(n²) String Operations

**Problem:**
```python
full_response = ""
async for event in shared_state.agent.astream(...):
    message, metadata = event
    if isinstance(message, (AIMessageChunk, AIMessage)):
        content = message.content
        if isinstance(content, str) and content:
            console.print(content, end="", style="blue", markup=False)
            full_response += content  # ⚠️ O(n²) string concatenation
            sys.stdout.flush()
```

**Impact:**
- Each `+=` creates a new string object in memory
- For long responses (1000+ tokens), this becomes O(n²) time complexity
- Memory churn and potential GC pressure

**Recommendation:**
```python
response_parts = []
async for event in shared_state.agent.astream(...):
    message, metadata = event
    if isinstance(message, (AIMessageChunk, AIMessage)):
        content = message.content
        if isinstance(content, str) and content:
            console.print(content, end="", style="blue", markup=False)
            response_parts.append(content)  # O(1) list append
            sys.stdout.flush()

full_response = "".join(response_parts)  # O(n) join operation
```

---

### 3. System Prompt File Re-read on Every Agent Init
**File:** `prompts/__init__.py:26-28`
**Severity:** MEDIUM
**Type:** Redundant I/O

**Problem:**
```python
def load_system_prompt() -> str:
    """Load the main system prompt for the coding agent."""
    return load_prompt("system_prompt")  # ⚠️ Reads from disk every time
```

**Impact:**
- File I/O on every agent initialization
- System prompt is static and never changes during execution
- Unnecessary disk access

**Recommendation:**
```python
_system_prompt_cache = None

def load_system_prompt() -> str:
    """Load the main system prompt for the coding agent (cached)."""
    global _system_prompt_cache
    if _system_prompt_cache is None:
        _system_prompt_cache = load_prompt("system_prompt")
    return _system_prompt_cache
```

---

## Medium Issues

### 4. Tool Instances Recreated on Every Call
**File:** `tools/get_tools.py:21-54`
**Severity:** MEDIUM
**Type:** Unnecessary Object Creation

**Problem:**
```python
async def get_tools() -> List[BaseTool]:
    # ⚠️ Creates new instances every time
    list_directory_tool = ListDirectoryTool()
    read_file_tool = ReadFileTool()
    write_file_tool = WriteFileTool()
    copy_file_tool = CopyFileTool()
    move_file_tool = MoveFileTool()
    delete_file_tool = DeleteFileTool()
    file_search_tool = FileSearchTool()
    search_tool = DuckDuckGoSearchRun()
    shell_tool = create_secure_shell_tool()

    mcp_tools = await get_mcp_tools()

    return [list_directory_tool, read_file_tool, ...]
```

**Impact:**
- 9 tool objects created from scratch on every call
- Combined with issue #1, tools are recreated on every model change
- Wasteful memory allocation

**Recommendation:**
```python
_cached_tools_list = None

async def get_tools() -> List[BaseTool]:
    global _cached_tools_list

    if _cached_tools_list is None:
        _cached_tools_list = [
            ListDirectoryTool(),
            ReadFileTool(),
            WriteFileTool(),
            CopyFileTool(),
            MoveFileTool(),
            DeleteFileTool(),
            FileSearchTool(),
            create_secure_shell_tool(),
            DuckDuckGoSearchRun(),
        ]

        mcp_tools = await get_mcp_tools()
        _cached_tools_list.extend(mcp_tools)

    return _cached_tools_list
```

---

### 5. Path Resolution Inside Validation Loop
**File:** `tools/secure_shell_tool.py:265-328`
**Severity:** MEDIUM
**Type:** Redundant Computation

**Problem:**
```python
def _validate_file_paths(self, args: List[str]) -> Optional[str]:
    for arg in args:
        # ... path checking logic ...
        is_valid = False
        for allowed_path in self.allowed_paths:
            allowed_resolved = Path(allowed_path).resolve()  # ⚠️ Resolves every time
            try:
                resolved_path.relative_to(allowed_resolved)
                is_valid = True
                break
            except ValueError:
                continue
```

**Impact:**
- `allowed_paths` are resolved on every command execution (line 311)
- Path resolution involves filesystem operations
- For `allowed_paths = [os.getcwd()]`, this is called repeatedly

**Recommendation:**
```python
def __init__(self, ...):
    super().__init__(**kwargs)
    # ... existing initialization ...

    # Pre-resolve allowed paths once
    self._resolved_allowed_paths = [Path(p).resolve() for p in self.allowed_paths]

def _validate_file_paths(self, args: List[str]) -> Optional[str]:
    for arg in args:
        # ... path checking logic ...
        is_valid = False
        for allowed_resolved in self._resolved_allowed_paths:  # Use cached
            try:
                resolved_path.relative_to(allowed_resolved)
                is_valid = True
                break
            except ValueError:
                continue
```

---

### 6. MCP Client Re-initialization Attempts
**File:** `tools/mcp.py:112-151`
**Severity:** MEDIUM
**Type:** Failed Initialization Retry

**Problem:**
```python
_client: Optional[MultiServerMCPClient] = None

def _get_client() -> Optional[MultiServerMCPClient]:
    global _client
    if _client is None:
        _client = create_mcp_client()  # ⚠️ Retries on every call if it fails
    return _client

async def get_mcp_tools() -> List[BaseTool]:
    client = _get_client()  # ⚠️ May retry failed initialization
    if client is None:
        return []

    try:
        return await client.get_tools()
    except ConnectionError as e:
        # ⚠️ Returns empty list but doesn't cache the failure
        return []
```

**Impact:**
- If MCP client creation fails (no config file, invalid config), it retries on every `get_tools()` call
- Wasted cycles attempting to recreate a client that will fail again
- Should use a sentinel value to cache failure

**Recommendation:**
```python
_client: Optional[MultiServerMCPClient] = None
_client_init_failed = False

def _get_client() -> Optional[MultiServerMCPClient]:
    global _client, _client_init_failed

    if _client_init_failed:
        return None

    if _client is None:
        _client = create_mcp_client()
        if _client is None:
            _client_init_failed = True

    return _client
```

---

### 7. New Callback Handler on Every Request
**File:** `main.py:190-192`
**Severity:** LOW-MEDIUM
**Type:** Unnecessary Object Creation

**Problem:**
```python
while True:
    # ... user input handling ...

    # ⚠️ Creates new callback handler for each request
    callback_handler = LoadingAndApprovalCallbackHandler(
        shared_approved_tools=shared_state.approved_tools
    )

    try:
        shared_state.messages.append(HumanMessage(content=user_input))
        callback_handler.start_loading("Processing your request...")
```

**Impact:**
- New handler object created for each user message
- Minimal impact since handlers are lightweight, but violates DRY
- Could reuse a single handler instance

**Recommendation:**
```python
# Initialize once before main loop
callback_handler = LoadingAndApprovalCallbackHandler(
    shared_approved_tools=shared_state.approved_tools
)

while True:
    # ... user input handling ...

    try:
        shared_state.messages.append(HumanMessage(content=user_input))
        callback_handler.start_loading("Processing your request...")
        # Reset state if necessary
        callback_handler.is_streaming = False
```

**Note:** This requires ensuring the callback handler is stateless or properly resets between uses.

---

## Low Priority Issues

### 8. Threading Lock in Single-threaded Context
**File:** `callbacks/loading_and_approval_callback_handler.py:34, 115`
**Severity:** LOW
**Type:** Unnecessary Synchronization

**Problem:**
```python
def __init__(self, shared_approved_tools: Optional[set] = None):
    # ...
    self.approval_lock = threading.Lock()  # ⚠️ Lock in async context

def on_tool_start(self, serialized, input_str, **kwargs):
    self.is_streaming = False
    self.stop_loading()

    # ...

    with self.approval_lock:  # ⚠️ Unnecessary in single-threaded async loop
        # ... approval UI ...
```

**Impact:**
- Minimal performance impact (lock acquire/release is fast when uncontended)
- Indicates architectural confusion between threading and async models
- The main loop is async/await based, not multi-threaded

**Recommendation:**
- Remove the lock unless there's a specific multi-threading scenario
- If LangChain callbacks can fire from multiple threads (unlikely in current setup), document why

---

### 9. Redundant hasattr Check in Dataclass
**File:** `config.py:74-93`
**Severity:** LOW
**Type:** Redundant Validation

**Problem:**
```python
def update_from_dict(self, updates: Dict[str, Any]) -> None:
    allowed_attrs = {
        "messages",
        "approved_tools",
        "current_provider",
        "current_model",
        "agent",
        "model_changed",
    }
    for key, value in updates.items():
        if key in allowed_attrs and hasattr(self, key):  # ⚠️ hasattr is redundant
            setattr(self, key, value)
```

**Impact:**
- `hasattr()` check is redundant for dataclass fields (they always exist)
- Very minor performance impact
- Set membership check in `allowed_attrs` is sufficient

**Recommendation:**
```python
def update_from_dict(self, updates: Dict[str, Any]) -> None:
    allowed_attrs = {
        "messages", "approved_tools", "current_provider",
        "current_model", "agent", "model_changed",
    }
    for key, value in updates.items():
        if key in allowed_attrs:  # hasattr check removed
            setattr(self, key, value)
```

---

### 10. Repeated Dictionary Lookups
**File:** `commands/command_handler.py:278-295`
**Severity:** LOW
**Type:** Minor Inefficiency

**Problem:**
```python
def show_status(self, args: List[str], state: dict) -> None:
    self.console.print("\n[bold cyan]Current Configuration:[/bold cyan]")

    provider = state.get("current_provider", "open_router")
    model = state.get("current_model", "xiaomi/mimo-v2-flash:free")

    self.console.print(
        f"  Provider: [green]{PROVIDERS.get(provider, {}).get('name', provider)}[/green]"
        # ⚠️ PROVIDERS.get() called inline
    )
    self.console.print(f"  Model: [green]{model}[/green]")
    self.console.print(
        f"  Conversation history: [green]{len(state.get('messages', []))} messages[/green]"
        # ⚠️ state.get() called multiple times for same key
    )
```

**Impact:**
- Multiple dictionary lookups for the same key
- Minimal impact due to O(1) dict access
- Code readability issue more than performance

**Recommendation:**
```python
def show_status(self, args: List[str], state: dict) -> None:
    self.console.print("\n[bold cyan]Current Configuration:[/bold cyan]")

    provider = state.get("current_provider", "open_router")
    model = state.get("current_model", "xiaomi/mimo-v2-flash:free")
    messages = state.get('messages', [])
    approved_tools = state.get('approved_tools', set())

    provider_info = PROVIDERS.get(provider, {})
    provider_name = provider_info.get('name', provider)

    self.console.print(f"  Provider: [green]{provider_name}[/green]")
    self.console.print(f"  Model: [green]{model}[/green]")
    self.console.print(f"  Conversation history: [green]{len(messages)} messages[/green]")
    self.console.print(f"  Approved tools: [green]{len(approved_tools)} tools[/green]")
```

---

### 11. No Default List in List Comprehension
**File:** `tools/secure_shell_tool.py:62-102, 105-150`
**Severity:** LOW
**Type:** Code Style (Minor Performance)

**Problem:**
The `default_allowed_commands` and `default_forbidden_commands` lists are defined in `__init__` rather than as class-level constants, meaning they're recreated for each tool instance.

**Recommendation:**
```python
# Define as class-level constants
DEFAULT_ALLOWED_COMMANDS = [
    "ls", "pwd", "echo", "cat", "head", "tail", "grep", "find",
    # ... rest of commands
]

DEFAULT_FORBIDDEN_COMMANDS = [
    "rm", "mv", "cp", "chmod", "chown", "mkdir", "touch", "dd",
    # ... rest of commands
]

class SecureShellTool(BaseTool):
    def __init__(self, ...):
        super().__init__(**kwargs)
        self.allowed_commands = allowed_commands or self.DEFAULT_ALLOWED_COMMANDS
        self.forbidden_commands = forbidden_commands or self.DEFAULT_FORBIDDEN_COMMANDS
```

---

## No N+1 Query Issues Found

This codebase does not interact with traditional databases (no SQL, ORM, or query builders), so classic N+1 query anti-patterns are not applicable. However, there are analogous patterns:

- **Tool re-initialization** (Issue #1) is similar to N+1 in that tools are fetched repeatedly when they could be cached
- **Path resolution in loops** (Issue #5) exhibits N+1-like behavior where resolution happens per-iteration

---

## No Re-render Issues Found

This is a CLI application without a traditional UI rendering pipeline. The Rich library is used for console output, but there are no inefficient re-render patterns detected. The streaming output (main.py:228) prints incrementally as designed.

---

## Summary of Recommendations

| Priority | Issue | Estimated Impact | Effort |
|----------|-------|-----------------|--------|
| HIGH | #1: Tool re-initialization | Saves 50-200ms per model change | Low |
| HIGH | #2: String concatenation | Saves O(n²) → O(n) for long responses | Low |
| MEDIUM | #3: System prompt caching | Saves 5-10ms per agent init | Low |
| MEDIUM | #4: Tool instance caching | Saves 20-50ms per call | Low |
| MEDIUM | #5: Path resolution caching | Saves 1-5ms per command | Medium |
| MEDIUM | #6: MCP failure caching | Prevents repeated failures | Low |
| LOW | #7: Callback handler reuse | Minimal savings | Medium |
| LOW | #8: Remove unnecessary lock | Architectural clarity | Low |
| LOW | #9-11: Code cleanup | Minimal impact | Low |

---

## Benchmarking Recommendations

To validate these findings, benchmark the following:

1. **Model change performance**: Time `initialize_agent()` before/after caching
2. **Streaming response**: Measure memory usage and time for 1000+ token responses
3. **Tool execution**: Profile `get_tools()` call frequency and duration
4. **Command validation**: Time `_validate_file_paths()` with cached vs. uncached paths

---

## Conclusion

The most impactful optimizations are:
1. **Cache tools and system prompt** across agent reinitializations
2. **Use list-based string building** instead of concatenation in streaming
3. **Pre-resolve allowed paths** in SecureShellTool

These changes would improve model switching responsiveness, reduce memory pressure during streaming, and optimize repeated command execution.
