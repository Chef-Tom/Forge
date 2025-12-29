"""Forge application configuration."""
from pathlib import Path

# Base paths
FORGE_ROOT = Path(__file__).parent.parent.resolve()
PROJECTS_ROOT = FORGE_ROOT / "projects"

# LLM settings (for later steps)
LLM_BASE_URL = "http://localhost:8080"

# Project structure constants
PROJECT_DIRS = ["docs", "chat", "meta", "history"]
REQUIRED_FILES = ["meta/project.yaml", "meta/summary.md", "chat/main.json"]
