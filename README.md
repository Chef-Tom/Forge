# Forge

**Codename: Hephaestus**

Local-first LLM-powered project workspace. Forge is a tool for managing multiple projects with integrated LLM assistance, automatic versioning, and structured conversation history.

## Overview

Forge provides a structured workspace for projects with:

- **Local-first architecture**: All data stored locally in human-readable formats
- **LLM integration**: Designed to work with local LLM servers (llama.cpp)
- **Automatic versioning**: Track changes to documentation and metadata
- **Conversation history**: Structured chat logs tied to each project
- **Project isolation**: Each project is self-contained with clear boundaries

## Current Status: Step 1 - Foundation

This is Step 1 of the phased build. The foundation layer includes:

- ✅ Project data models (Pydantic schemas)
- ✅ Core project services (create, list, open, get)
- ✅ File structure and path utilities
- ✅ Configuration management
- ✅ Comprehensive test suite

**Not yet implemented**: API endpoints, CLI interface, LLM integration, versioning system

## Setup

### Prerequisites

- Python 3.12 or higher
- pyenv (recommended for Python version management)

### Installation

1. Clone the repository and navigate to it:
   ```bash
   cd /path/to/Forge
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Linux/Mac
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Project Structure

```
Forge/
├── server/              # Application code
│   ├── models/          # Data models (Pydantic)
│   │   └── project.py   # Project metadata and conversation schemas
│   ├── services/        # Business logic
│   │   └── project_service.py
│   ├── utils/           # Helper utilities
│   │   └── paths.py     # Path management
│   └── config.py        # Application configuration
├── projects/            # User projects (each is isolated)
│   └── .gitkeep
├── tests/               # Test suite
│   └── test_project_creation.py
├── pyproject.toml       # Dependencies and build config
└── README.md
```

## Running Tests

Run the full test suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run with coverage:

```bash
pytest --cov=server --cov-report=html
```

## Usage

Currently, Forge can be used programmatically via Python:

```python
from server.services.project_service import create_project, list_projects, open_project

# Create a new project
meta = create_project(
    project_id="my-cool-project",
    name="My Cool Project",
    description="A project for building something awesome"
)
print(f"Created: {meta.name}")

# List all projects
for project in list_projects():
    print(f"- {project.id}: {project.name}")

# Open a project (updates last_opened_at timestamp)
meta = open_project("my-cool-project")
print(f"Opened: {meta.name}")
```

## Project Format

Each project created by Forge follows this structure:

```
my-project/
├── docs/                # Markdown documentation
│   └── index.md         # Project index page
├── chat/                # Conversation logs
│   └── main.json        # Main conversation thread
├── meta/                # Project metadata
│   ├── project.yaml     # Project configuration
│   └── summary.md       # Human-readable project summary
└── history/             # Auto-versioning snapshots (future)
    ├── docs/
    └── meta/
```

### Project Metadata Schema

Projects are defined by `meta/project.yaml`:

```yaml
id: my-project
name: My Project
description: What this project is about
created_at: 2025-01-15T10:30:00Z
last_opened_at: 2025-01-15T14:20:00Z
status: active  # active | paused | archived
rules:
  allow_cross_project_access: false
  llm_edit_scope: markdown_only
  max_llm_edit_size: 500
```

### Conversation Schema

Chat logs are stored in `chat/main.json`:

```json
{
  "conversation_id": "main",
  "created_at": "2025-01-15T10:30:00Z",
  "messages": [
    {
      "id": "msg-1",
      "timestamp": "2025-01-15T10:31:00Z",
      "role": "user",
      "content": "What should we work on first?"
    },
    {
      "id": "msg-2",
      "timestamp": "2025-01-15T10:31:05Z",
      "role": "assistant",
      "content": "Based on the project summary..."
    }
  ]
}
```

## Configuration

Default configuration is in `server/config.py`:

- **FORGE_ROOT**: Repository root directory (auto-detected)
- **PROJECTS_ROOT**: Where user projects are stored (`{FORGE_ROOT}/projects`)
- **LLM_BASE_URL**: llama.cpp server URL (default: `http://localhost:8080`)

## Design Principles

1. **Local-first**: All data stored locally in human-readable formats (YAML, Markdown, JSON)
2. **Transparency**: No hidden state or binary formats
3. **Git-friendly**: All project files are designed to work well with version control
4. **LLM-native**: Structure optimized for LLM context windows and reasoning
5. **Simplicity**: Minimal abstractions, clear boundaries

## Development Roadmap

### ✅ Step 1: Foundation (Current)
- Directory structure and data models
- Core project services
- Test suite

### 🔄 Step 2: Versioning System (Next)
- Auto-snapshot on file changes
- File read/write utilities with history tracking
- Diff and rollback capabilities

### 📋 Step 3: LLM Integration (Future)
- llama.cpp integration
- Conversation management
- Context window optimization

### 📋 Step 4: API & CLI (Future)
- RESTful API endpoints
- Command-line interface
- Project workspace commands

## Testing

The test suite covers:

- ✅ Project creation with proper directory structure
- ✅ YAML metadata generation and validation
- ✅ Summary template generation
- ✅ Empty conversation initialization
- ✅ Duplicate project prevention
- ✅ Project ID validation
- ✅ Project listing and sorting
- ✅ Project opening with timestamp updates

## Contributing

This is a personal project in early development. The architecture and design may change significantly as it evolves.

## License

To be determined.

## Questions & Notes

### Open Design Questions

1. Should `project_id` allow underscores, or hyphens only? (Currently: hyphens only)
2. Should tests use a separate test directory? (Currently: uses main projects directory with cleanup)
3. What additional metadata fields might be needed for specific use cases?

### Notes from Planning

This project emerged from a need for better project management when working with LLMs. The goal is to provide structure without sacrificing flexibility, and to keep everything transparent and inspectable.

The architecture is designed to be simple enough to understand completely, while powerful enough to handle real project work.
