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
