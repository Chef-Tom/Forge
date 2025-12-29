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
