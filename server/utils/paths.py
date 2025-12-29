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
