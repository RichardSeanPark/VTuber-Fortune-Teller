# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Package Management
All dependencies are managed with `uv` (version ~= 0.8). Always use these commands:
- **Install dependencies**: `uv sync`
- **Add package**: `uv add <package>`
- **Remove package**: `uv remove <package>`
- **Run any command**: `uv run <command>`
- **Update project**: `uv run upgrade.py`

### Running the Application
- **Start server**: `uv run python run_server.py`
- **Run with specific config**: `uv run python run_server.py --conf <config_file>`
- **Check version**: `uv run python run_server.py --version`

### Code Quality
- **Format code**: `uv run ruff format`
- **Lint code**: `uv run ruff check`
- **Fix linting issues**: `uv run ruff check --fix`
- **Pre-commit hooks**: `uv run pre-commit run --all-files`

### Testing
Currently, the project does not have automated tests configured. Testing is done manually by running the application and verifying functionality.

## High-Level Architecture

### Core System Design
The project follows a modular, plugin-based architecture with strict separation between frontend and backend:

1. **WebSocket-Based Communication**: Real-time bidirectional communication between frontend (React) and backend (FastAPI) via WebSocket connections. All client interactions go through `/client-ws` endpoint.

2. **Service Context Pattern**: The `ServiceContext` class acts as a dependency injection container, managing all service instances (ASR, TTS, Agent, VAD, etc.) and their lifecycle. Each WebSocket session gets its own context instance.

3. **Agent System**: Implements a flexible agent architecture where different LLM backends (OpenAI, Ollama, Claude, etc.) can be swapped via configuration. The agent handles conversation state, memory, and response generation.

4. **Conversation Management**: Two conversation types:
   - **SingleConversation**: Direct 1-on-1 interactions with the AI
   - **GroupConversation**: Multi-participant conversations with role management

5. **Plugin-Based Modules**: All major components (ASR, TTS, Agent, Translation, Live2D) follow an interface pattern with factory methods, allowing easy extension and swapping of implementations.

### Critical Performance Requirements
- **Primary Goal**: End-to-end latency < 500ms (user speaks → AI voice heard)
- **Async-First Design**: All I/O operations must be async to prevent blocking
- **Stream Processing**: Audio and text are processed in streaming fashion to minimize latency

### Configuration System
The configuration uses a Pydantic-validated YAML system:
- **Templates**: `config_templates/conf.default.yaml` (English) and `conf.ZH.default.yaml` (Chinese)
- **Validation**: `src/open_llm_vtuber/config_manager/main.py` contains all Pydantic models
- **User Config**: `conf.yaml` is generated from templates and validated on load

### Module Communication Flow
```
User Voice → ASR → Agent → TTS → Audio Output
     ↓         ↓      ↓      ↓
  WebSocket  Message  Live2D  Frontend
   Handler   Queue   Updates  Display
```

### Key Directories
- `src/open_llm_vtuber/agent/`: LLM agents and stateless LLM implementations
- `src/open_llm_vtuber/asr/`: Speech recognition modules (Whisper, SherpaOnnx, etc.)
- `src/open_llm_vtuber/tts/`: Text-to-speech modules (Edge TTS, Azure, GPTSoVITS, etc.)
- `src/open_llm_vtuber/conversations/`: Conversation handling and TTS management
- `src/open_llm_vtuber/mcpp/`: MCP (Model Context Protocol) client integration
- `frontend/`: Pre-built React frontend (git submodule)

### Extension Points
To add new functionality:
1. **New LLM**: Implement `StatelessLLMInterface` in `agent/stateless_llm/`
2. **New ASR**: Implement `ASRInterface` in `asr/`
3. **New TTS**: Implement `TTSInterface` in `tts/`
4. **New Agent**: Implement `AgentInterface` in `agent/agents/`

## Important Coding Standards

### Type Hints (Python 3.10+)
- Use `|` for unions: `str | None` (NOT `Optional[str]`)
- Use built-in generics: `list[int]`, `dict[str, float]` (NOT `List`, `Dict` from typing)
- All functions must have complete type hints

### Async Best Practices
- Never use blocking I/O in async contexts
- Use `asyncio.create_task()` for concurrent operations
- Prefer `asyncio.gather()` for waiting on multiple coroutines

### Configuration Changes
When modifying configuration:
1. Update BOTH `conf.default.yaml` and `conf.ZH.default.yaml` templates
2. Update Pydantic models in `src/open_llm_vtuber/config_manager/`
3. Run the application to verify validation works

### Dependency Management
- First try to solve with standard library or existing dependencies
- When adding dependencies: `uv add <package>` then manually update `requirements.txt`
- All dependencies must be cross-platform compatible (Windows, macOS, Linux)

### Logging
- Use `loguru` for all logging (already configured in `run_server.py`)
- Log messages in English with appropriate levels
- Include context in log messages for debugging

## Platform Considerations

### Cross-Platform Requirements
- Core functionality MUST work offline on all platforms
- Platform-specific features (CUDA, Windows-only APIs) must be optional with graceful fallbacks
- File paths must use `pathlib.Path` for cross-platform compatibility

### Frontend Integration
- Frontend is a separate React repository integrated via git submodule
- Frontend artifacts are in `frontend/` directory
- Do not modify frontend files directly - they come from the submodule

### Model Storage
Models are stored locally in the `models/` directory with environment variables:
- `HF_HOME` and `MODELSCOPE_CACHE` are set to `./models`
- This keeps all model files within the project directory