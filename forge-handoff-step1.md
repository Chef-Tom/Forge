# Forge - Step 1: Foundation Setup

## Context for Claude Code

You are helping build **Forge** (codename: Hephaestus), a local-first LLM-powered project workspace. This is Step 1 of a phased build. Your job is to establish the folder structure and data formats that everything else depends on.

**Do not** build the API, CLI, or LLM integration yet. Just the foundation.

---

## Environment

- **OS**: Linux (Ubuntu, likely)
- **Python**: 3.12 via pyenv
- **Project root**: `/opt/forge/`
- **LLM**: llama.cpp in server mode at `http://localhost:8080` (not used in this step)

---

## Task 1: Create Application Folder Structure

Create the following structure at `/opt/forge/`:

```
/opt/forge/
├── server/                  # Python application code
│   ├── __init__.py
│   ├── models/              # Data models (Pydantic)
│   │   ├── __init__.py
│   │   └── project.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   └── project_service.py
│   ├── utils/               # Helpers
│   │   ├── __init__.py
│   │   └── paths.py
│   └── config.py            # Application configuration
├── projects/                # Where user projects live
│   └── .gitkeep
├── tests/                   # Test files
│   ├── __init__.py
│   └── test_project_creation.py
├── pyproject.toml           # Project dependencies
└── README.md
```

---

## Task 2: Define Configuration (`server/config.py`)

Create a simple configuration module:

```python
"""Forge application configuration."""
from pathlib import Path

# Base paths
FORGE_ROOT = Path("/opt/forge")
PROJECTS_ROOT = FORGE_ROOT / "projects"

# LLM settings (for later steps)
LLM_BASE_URL = "http://localhost:8080"

# Project structure constants
PROJECT_DIRS = ["docs", "chat", "meta", "history"]
REQUIRED_FILES = ["meta/project.yaml", "meta/summary.md", "chat/main.json"]
```

---

## Task 3: Define Data Models (`server/models/project.py`)

Using Pydantic, define the data structures. These match the spec in the planning documents.

### project.yaml schema

```python
"""Data models for Forge projects."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """Project lifecycle status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ProjectRules(BaseModel):
    """Constraints the LLM must follow for this project."""
    allow_cross_project_access: bool = False
    llm_edit_scope: str = "markdown_only"
    max_llm_edit_size: int = 500  # lines


class ProjectMeta(BaseModel):
    """
    Schema for meta/project.yaml
    
    This defines what the project IS, not what's in it.
    """
    id: str = Field(..., pattern=r"^[a-z0-9-]+$", description="URL-safe project identifier")
    name: str = Field(..., min_length=1, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_opened_at: Optional[datetime] = None
    description: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    rules: ProjectRules = Field(default_factory=ProjectRules)


class ChatMessage(BaseModel):
    """A single message in a conversation."""
    id: str
    timestamp: datetime
    role: str = Field(..., pattern=r"^(user|assistant|system)$")
    content: str


class Conversation(BaseModel):
    """
    Schema for chat/main.json
    
    The single conversation thread for Phase 1.
    """
    conversation_id: str = "main"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    messages: list[ChatMessage] = Field(default_factory=list)
```

---

## Task 4: Create Path Utilities (`server/utils/paths.py`)

```python
"""Path utilities for Forge projects."""
from pathlib import Path
from server.config import PROJECTS_ROOT


def get_project_path(project_id: str) -> Path:
    """Get the root path for a project."""
    return PROJECTS_ROOT / project_id


def get_project_docs_path(project_id: str) -> Path:
    """Get the docs folder for a project."""
    return get_project_path(project_id) / "docs"


def get_project_chat_path(project_id: str) -> Path:
    """Get the chat folder for a project."""
    return get_project_path(project_id) / "chat"


def get_project_meta_path(project_id: str) -> Path:
    """Get the meta folder for a project."""
    return get_project_path(project_id) / "meta"


def get_project_history_path(project_id: str) -> Path:
    """Get the history folder for a project."""
    return get_project_path(project_id) / "history"


def project_exists(project_id: str) -> bool:
    """Check if a project exists."""
    return get_project_path(project_id).is_dir()
```

---

## Task 5: Create Project Service (`server/services/project_service.py`)

This is the core logic for creating projects with the correct structure.

```python
"""Project management service."""
import json
from datetime import datetime
from pathlib import Path

import yaml

from server.config import PROJECT_DIRS
from server.models.project import ProjectMeta, Conversation
from server.utils.paths import (
    get_project_path,
    get_project_meta_path,
    get_project_chat_path,
    get_project_docs_path,
    get_project_history_path,
    project_exists,
)


class ProjectExistsError(Exception):
    """Raised when trying to create a project that already exists."""
    pass


class ProjectNotFoundError(Exception):
    """Raised when a project doesn't exist."""
    pass


def create_project(project_id: str, name: str, description: str = "") -> ProjectMeta:
    """
    Create a new project with the canonical folder structure.
    
    Args:
        project_id: URL-safe identifier (lowercase, hyphens only)
        name: Human-readable project name
        description: Optional project description
        
    Returns:
        ProjectMeta: The created project's metadata
        
    Raises:
        ProjectExistsError: If project already exists
        ValueError: If project_id is invalid
    """
    # Validate project_id format
    if not project_id or not project_id.replace("-", "").isalnum():
        raise ValueError(f"Invalid project_id: {project_id}. Use lowercase letters, numbers, and hyphens only.")
    
    if project_id != project_id.lower():
        raise ValueError(f"Project ID must be lowercase: {project_id}")
    
    if project_exists(project_id):
        raise ProjectExistsError(f"Project already exists: {project_id}")
    
    # Create directory structure
    project_path = get_project_path(project_id)
    
    for dir_name in PROJECT_DIRS:
        (project_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    # Create history subdirectories
    (get_project_history_path(project_id) / "docs").mkdir(exist_ok=True)
    (get_project_history_path(project_id) / "meta").mkdir(exist_ok=True)
    
    # Create project metadata
    meta = ProjectMeta(
        id=project_id,
        name=name,
        description=description,
        created_at=datetime.utcnow(),
    )
    
    # Write project.yaml
    meta_path = get_project_meta_path(project_id) / "project.yaml"
    with open(meta_path, "w") as f:
        yaml.dump(meta.model_dump(mode="json"), f, default_flow_style=False, sort_keys=False)
    
    # Create summary.md with template
    summary_path = get_project_meta_path(project_id) / "summary.md"
    summary_template = f"""# Project Summary

## Intent
{description or "[Describe what this project is trying to achieve]"}

## Current Focus
[What are you working on right now?]

## Constraints
- [List any hard constraints or rules]

## Open Questions
- [What decisions are pending?]

## Last Known Good State
[What was working last time you touched this?]

## Notes to Future Me
[Anything you'll forget but shouldn't]
"""
    with open(summary_path, "w") as f:
        f.write(summary_template)
    
    # Create empty chat log
    chat_path = get_project_chat_path(project_id) / "main.json"
    conversation = Conversation(
        conversation_id="main",
        created_at=datetime.utcnow(),
        messages=[],
    )
    with open(chat_path, "w") as f:
        json.dump(conversation.model_dump(mode="json"), f, indent=2)
    
    # Create index.md in docs
    index_path = get_project_docs_path(project_id) / "index.md"
    with open(index_path, "w") as f:
        f.write(f"# {name}\n\n{description}\n")
    
    return meta


def list_projects() -> list[ProjectMeta]:
    """
    List all projects.
    
    Returns:
        List of ProjectMeta for all valid projects
    """
    from server.config import PROJECTS_ROOT
    
    projects = []
    
    if not PROJECTS_ROOT.exists():
        return projects
    
    for path in PROJECTS_ROOT.iterdir():
        if not path.is_dir():
            continue
        
        meta_file = path / "meta" / "project.yaml"
        if not meta_file.exists():
            continue
        
        try:
            with open(meta_file) as f:
                data = yaml.safe_load(f)
                projects.append(ProjectMeta(**data))
        except Exception:
            # Skip invalid projects
            continue
    
    return sorted(projects, key=lambda p: p.last_opened_at or p.created_at, reverse=True)


def open_project(project_id: str) -> ProjectMeta:
    """
    Open a project (updates last_opened_at timestamp).
    
    Args:
        project_id: The project identifier
        
    Returns:
        ProjectMeta: The project's metadata
        
    Raises:
        ProjectNotFoundError: If project doesn't exist
    """
    if not project_exists(project_id):
        raise ProjectNotFoundError(f"Project not found: {project_id}")
    
    meta_path = get_project_meta_path(project_id) / "project.yaml"
    
    with open(meta_path) as f:
        data = yaml.safe_load(f)
    
    meta = ProjectMeta(**data)
    meta.last_opened_at = datetime.utcnow()
    
    with open(meta_path, "w") as f:
        yaml.dump(meta.model_dump(mode="json"), f, default_flow_style=False, sort_keys=False)
    
    return meta


def get_project(project_id: str) -> ProjectMeta:
    """
    Get project metadata without updating timestamps.
    
    Args:
        project_id: The project identifier
        
    Returns:
        ProjectMeta: The project's metadata
        
    Raises:
        ProjectNotFoundError: If project doesn't exist
    """
    if not project_exists(project_id):
        raise ProjectNotFoundError(f"Project not found: {project_id}")
    
    meta_path = get_project_meta_path(project_id) / "project.yaml"
    
    with open(meta_path) as f:
        data = yaml.safe_load(f)
    
    return ProjectMeta(**data)
```

---

## Task 6: Create pyproject.toml

```toml
[project]
name = "forge"
version = "0.1.0"
description = "Local-first LLM-powered project workspace"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

---

## Task 7: Create Tests (`tests/test_project_creation.py`)

```python
"""Tests for project creation and management."""
import json
import shutil
from pathlib import Path

import pytest
import yaml

from server.config import PROJECTS_ROOT
from server.services.project_service import (
    create_project,
    list_projects,
    open_project,
    get_project,
    ProjectExistsError,
    ProjectNotFoundError,
)


@pytest.fixture(autouse=True)
def clean_test_projects():
    """Clean up test projects before and after each test."""
    test_ids = ["test-project", "test-project-2"]
    
    for project_id in test_ids:
        path = PROJECTS_ROOT / project_id
        if path.exists():
            shutil.rmtree(path)
    
    yield
    
    for project_id in test_ids:
        path = PROJECTS_ROOT / project_id
        if path.exists():
            shutil.rmtree(path)


class TestCreateProject:
    """Tests for project creation."""
    
    def test_creates_directory_structure(self):
        """Project creation should create all required directories."""
        create_project("test-project", "Test Project")
        
        project_path = PROJECTS_ROOT / "test-project"
        
        assert project_path.exists()
        assert (project_path / "docs").is_dir()
        assert (project_path / "chat").is_dir()
        assert (project_path / "meta").is_dir()
        assert (project_path / "history").is_dir()
        assert (project_path / "history" / "docs").is_dir()
        assert (project_path / "history" / "meta").is_dir()
    
    def test_creates_project_yaml(self):
        """Project creation should create valid project.yaml."""
        create_project("test-project", "Test Project", "A test description")
        
        meta_path = PROJECTS_ROOT / "test-project" / "meta" / "project.yaml"
        assert meta_path.exists()
        
        with open(meta_path) as f:
            data = yaml.safe_load(f)
        
        assert data["id"] == "test-project"
        assert data["name"] == "Test Project"
        assert data["description"] == "A test description"
        assert data["status"] == "active"
        assert "created_at" in data
    
    def test_creates_summary_md(self):
        """Project creation should create summary.md with template."""
        create_project("test-project", "Test Project")
        
        summary_path = PROJECTS_ROOT / "test-project" / "meta" / "summary.md"
        assert summary_path.exists()
        
        content = summary_path.read_text()
        assert "# Project Summary" in content
        assert "## Intent" in content
        assert "## Current Focus" in content
    
    def test_creates_empty_chat_log(self):
        """Project creation should create empty chat log."""
        create_project("test-project", "Test Project")
        
        chat_path = PROJECTS_ROOT / "test-project" / "chat" / "main.json"
        assert chat_path.exists()
        
        with open(chat_path) as f:
            data = json.load(f)
        
        assert data["conversation_id"] == "main"
        assert data["messages"] == []
    
    def test_creates_index_md(self):
        """Project creation should create index.md in docs."""
        create_project("test-project", "Test Project")
        
        index_path = PROJECTS_ROOT / "test-project" / "docs" / "index.md"
        assert index_path.exists()
        
        content = index_path.read_text()
        assert "# Test Project" in content
    
    def test_rejects_duplicate_project(self):
        """Cannot create a project that already exists."""
        create_project("test-project", "Test Project")
        
        with pytest.raises(ProjectExistsError):
            create_project("test-project", "Test Project Again")
    
    def test_rejects_invalid_project_id(self):
        """Project ID must be lowercase with hyphens only."""
        with pytest.raises(ValueError):
            create_project("Test_Project", "Test Project")
        
        with pytest.raises(ValueError):
            create_project("TEST", "Test Project")
        
        with pytest.raises(ValueError):
            create_project("test project", "Test Project")


class TestListProjects:
    """Tests for listing projects."""
    
    def test_lists_created_projects(self):
        """Should list all created projects."""
        create_project("test-project", "Test Project")
        create_project("test-project-2", "Test Project 2")
        
        projects = list_projects()
        ids = [p.id for p in projects]
        
        assert "test-project" in ids
        assert "test-project-2" in ids
    
    def test_empty_list_when_no_projects(self):
        """Should return empty list when no projects exist."""
        # Note: This might fail if other projects exist
        # In a real setup, we'd use a test-specific projects directory
        projects = list_projects()
        test_ids = [p.id for p in projects if p.id.startswith("test-")]
        assert len(test_ids) == 0


class TestOpenProject:
    """Tests for opening projects."""
    
    def test_updates_last_opened_at(self):
        """Opening a project should update last_opened_at."""
        meta = create_project("test-project", "Test Project")
        assert meta.last_opened_at is None
        
        opened = open_project("test-project")
        assert opened.last_opened_at is not None
    
    def test_raises_for_missing_project(self):
        """Should raise error for non-existent project."""
        with pytest.raises(ProjectNotFoundError):
            open_project("nonexistent-project")


class TestGetProject:
    """Tests for getting project metadata."""
    
    def test_returns_project_meta(self):
        """Should return project metadata."""
        create_project("test-project", "Test Project", "Description")
        
        meta = get_project("test-project")
        
        assert meta.id == "test-project"
        assert meta.name == "Test Project"
        assert meta.description == "Description"
    
    def test_raises_for_missing_project(self):
        """Should raise error for non-existent project."""
        with pytest.raises(ProjectNotFoundError):
            get_project("nonexistent-project")
```

---

## Task 8: Create README.md

```markdown
# Forge

Local-first LLM-powered project workspace.

## Setup

1. Ensure Python 3.12+ is available (via pyenv)
2. Create virtual environment:
   ```bash
   cd /opt/forge
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Project Structure

```
/opt/forge/
├── server/          # Application code
├── projects/        # User projects (each is isolated)
├── tests/           # Test suite
└── pyproject.toml   # Dependencies
```

## Running Tests

```bash
pytest
```

## Project Format

Each project follows this structure:

```
project-name/
├── docs/            # Markdown documents
├── chat/            # Conversation logs
│   └── main.json
├── meta/            # Project metadata
│   ├── project.yaml
│   └── summary.md
└── history/         # Auto-versioning snapshots
    ├── docs/
    └── meta/
```
```

---

## Verification Steps

After implementing, verify with:

1. **Create the directory structure**:
   ```bash
   sudo mkdir -p /opt/forge
   sudo chown $USER:$USER /opt/forge
   ```

2. **Set up Python environment**:
   ```bash
   cd /opt/forge
   pyenv local 3.12
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Run tests**:
   ```bash
   pytest -v
   ```

4. **Manual verification** (Python REPL):
   ```python
   from server.services.project_service import create_project, list_projects
   
   # Create test project
   meta = create_project("65816-minicomputer", "65816 Minicomputer", 
       "Design and implementation of a 65816-based homebrew minicomputer")
   print(f"Created: {meta.name}")
   
   # List projects
   for p in list_projects():
       print(f"- {p.id}: {p.name}")
   ```

5. **Verify folder structure**:
   ```bash
   tree /opt/forge/projects/65816-minicomputer/
   ```

---

## Success Criteria

Step 1 is complete when:

- [ ] All directories exist at `/opt/forge/`
- [ ] `pytest` passes all tests
- [ ] Can create a project via Python
- [ ] Project has correct folder structure
- [ ] `project.yaml` is valid YAML with correct schema
- [ ] `summary.md` exists with template content
- [ ] `main.json` exists with empty messages array

---

## Questions for Human Liaison

If anything is unclear:

1. Should `project_id` allow underscores, or hyphens only?
2. Should tests use a separate test directory, or is it okay to create/delete in `/opt/forge/projects/`?
3. Any additional fields needed in `project.yaml` for your 65816 project?

---

## Next Step Preview

Once this is verified, Step 2 will add:
- The versioning system (auto-snapshot on file changes)
- File read/write utilities with history tracking
