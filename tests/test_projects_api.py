"""
Unit tests for the Projects API module.

Tests cover:
- list_projects: Paginated projects listing
- get_project: Retrieve single project
- create_project: Create new project
- update_project: Update project metadata
- delete_project: Delete project
- archive_project / restore_project: Archive/restore projects
- get_project_entries: Get BOM entries
- add_project_entries: Add BOM entries
- update_project_entries: Update BOM entries
- delete_project_entries: Delete BOM entries
- get_project_builds: List builds
- get_build / update_build: Build operations
"""

import pytest

from partsbox_mcp.api.projects import (
    add_project_entries,
    archive_project,
    create_project,
    delete_project,
    delete_project_entries,
    get_build,
    get_project,
    get_project_builds,
    get_project_entries,
    list_projects,
    restore_project,
    update_build,
    update_project,
    update_project_entries,
)
from partsbox_mcp.client import cache


class TestListProjects:
    """Tests for the list_projects tool function."""

    def test_list_projects_returns_non_archived(self, fake_api_active):
        """list_projects returns non-archived projects by default."""
        result = list_projects()

        assert result.success is True
        assert result.total == 2  # 2 non-archived + 1 archived
        assert result.error is None

    def test_list_projects_includes_archived(self, fake_api_active):
        """list_projects includes archived when requested."""
        result = list_projects(include_archived=True)

        assert result.success is True
        assert result.total == 3  # All 3 projects

    def test_list_projects_returns_cache_key(self, fake_api_active):
        """list_projects returns a valid cache key."""
        result = list_projects()

        assert result.success is True
        assert result.cache_key is not None
        assert result.cache_key.startswith("pb_")

    def test_list_projects_pagination_limit(self, fake_api_active):
        """list_projects respects the limit parameter."""
        result = list_projects(limit=1)

        assert result.success is True
        assert len(result.data) == 1
        assert result.has_more is True

    def test_list_projects_cache_reuse(self, fake_api_active):
        """list_projects reuses cached data."""
        result1 = list_projects(limit=1)
        cache_key = result1.cache_key

        result2 = list_projects(limit=1, offset=1, cache_key=cache_key)

        assert result2.success is True
        assert result2.cache_key == cache_key


class TestListProjectsJMESPath:
    """Tests for JMESPath query support in list_projects."""

    def test_query_filter_by_name(self, fake_api_active):
        """JMESPath filter by name works."""
        result = list_projects(query='[?contains("project/name", \'Arduino\')]')

        assert result.success is True
        assert result.total == 1  # Only Arduino Shield

    def test_query_projection(self, fake_api_active):
        """JMESPath projection works."""
        result = list_projects(query='[*].{name: "project/name", entries: "project/entry-count"}')

        assert result.success is True
        first = result.data[0]
        assert "name" in first
        assert "entries" in first


class TestGetProject:
    """Tests for the get_project tool function."""

    def test_get_project_success(self, fake_api_active):
        """get_project returns the correct project."""
        result = get_project("proj_001")

        assert result.success is True
        assert result.data is not None
        assert result.data["project/id"] == "proj_001"
        assert result.data["project/name"] == "Arduino Shield v1"

    def test_get_project_not_found(self, fake_api_active):
        """get_project returns error for non-existent project."""
        result = get_project("nonexistent_proj")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_get_project_empty_id(self, fake_api_active):
        """get_project returns error for empty project_id."""
        result = get_project("")

        assert result.success is False
        assert "project_id is required" in result.error


class TestCreateProject:
    """Tests for the create_project tool function."""

    def test_create_project_success(self, fake_api_active):
        """create_project successfully creates a project."""
        result = create_project(name="New Project")

        assert result.success is True
        assert result.data is not None
        assert result.data["project/name"] == "New Project"

    def test_create_project_with_description(self, fake_api_active):
        """create_project works with description."""
        result = create_project(
            name="Test Project",
            description="A test project description",
        )

        assert result.success is True

    def test_create_project_missing_name(self, fake_api_active):
        """create_project returns error for missing name."""
        result = create_project(name="")

        assert result.success is False
        assert "name is required" in result.error


class TestUpdateProject:
    """Tests for the update_project tool function."""

    def test_update_project_success(self, fake_api_active):
        """update_project successfully updates a project."""
        result = update_project(
            project_id="proj_001",
            name="Updated Project Name",
        )

        assert result.success is True

    def test_update_project_with_description(self, fake_api_active):
        """update_project works with description update."""
        result = update_project(
            project_id="proj_001",
            description="Updated description",
        )

        assert result.success is True

    def test_update_project_missing_id(self, fake_api_active):
        """update_project returns error for missing project_id."""
        result = update_project(project_id="")

        assert result.success is False
        assert "project_id is required" in result.error


class TestDeleteProject:
    """Tests for the delete_project tool function."""

    def test_delete_project_success(self, fake_api_active):
        """delete_project successfully deletes a project."""
        result = delete_project("proj_001")

        assert result.success is True

    def test_delete_project_missing_id(self, fake_api_active):
        """delete_project returns error for missing project_id."""
        result = delete_project("")

        assert result.success is False
        assert "project_id is required" in result.error


class TestArchiveRestoreProject:
    """Tests for archive and restore project functions."""

    def test_archive_project_success(self, fake_api_active):
        """archive_project successfully archives a project."""
        result = archive_project("proj_001")

        assert result.success is True

    def test_archive_project_missing_id(self, fake_api_active):
        """archive_project returns error for missing project_id."""
        result = archive_project("")

        assert result.success is False
        assert "project_id is required" in result.error

    def test_restore_project_success(self, fake_api_active):
        """restore_project successfully restores a project."""
        result = restore_project("proj_archived")

        assert result.success is True

    def test_restore_project_missing_id(self, fake_api_active):
        """restore_project returns error for missing project_id."""
        result = restore_project("")

        assert result.success is False
        assert "project_id is required" in result.error


class TestGetProjectEntries:
    """Tests for the get_project_entries tool function."""

    def test_get_entries_success(self, fake_api_active):
        """get_project_entries returns BOM entries."""
        result = get_project_entries("proj_001")

        assert result.success is True
        assert result.total == 3  # Arduino Shield has 3 entries

    def test_get_entries_missing_id(self, fake_api_active):
        """get_project_entries returns error for missing project_id."""
        result = get_project_entries("")

        assert result.success is False
        assert "project_id is required" in result.error

    def test_get_entries_pagination(self, fake_api_active):
        """get_project_entries supports pagination."""
        result = get_project_entries("proj_001", limit=2)

        assert result.success is True
        assert len(result.data) == 2
        assert result.has_more is True


class TestAddProjectEntries:
    """Tests for the add_project_entries tool function."""

    def test_add_entries_success(self, fake_api_active):
        """add_project_entries successfully adds entries."""
        entries = [
            {"entry/part-id": "part_001", "entry/quantity": 5},
        ]
        result = add_project_entries("proj_001", entries)

        assert result.success is True

    def test_add_entries_missing_project_id(self, fake_api_active):
        """add_project_entries returns error for missing project_id."""
        result = add_project_entries("", [{"entry/part-id": "part_001", "entry/quantity": 1}])

        assert result.success is False
        assert "project_id is required" in result.error

    def test_add_entries_missing_entries(self, fake_api_active):
        """add_project_entries returns error for missing entries."""
        result = add_project_entries("proj_001", [])

        assert result.success is False
        assert "entries is required" in result.error


class TestUpdateProjectEntries:
    """Tests for the update_project_entries tool function."""

    def test_update_entries_success(self, fake_api_active):
        """update_project_entries successfully updates entries."""
        entries = [
            {"entry/id": "entry_001", "entry/quantity": 15},
        ]
        result = update_project_entries("proj_001", entries)

        assert result.success is True

    def test_update_entries_missing_project_id(self, fake_api_active):
        """update_project_entries returns error for missing project_id."""
        result = update_project_entries("", [{"entry/id": "entry_001"}])

        assert result.success is False
        assert "project_id is required" in result.error


class TestDeleteProjectEntries:
    """Tests for the delete_project_entries tool function."""

    def test_delete_entries_success(self, fake_api_active):
        """delete_project_entries successfully deletes entries."""
        result = delete_project_entries("proj_001", ["entry_001"])

        assert result.success is True

    def test_delete_entries_missing_project_id(self, fake_api_active):
        """delete_project_entries returns error for missing project_id."""
        result = delete_project_entries("", ["entry_001"])

        assert result.success is False
        assert "project_id is required" in result.error

    def test_delete_entries_missing_entry_ids(self, fake_api_active):
        """delete_project_entries returns error for missing entry_ids."""
        result = delete_project_entries("proj_001", [])

        assert result.success is False
        assert "entry_ids is required" in result.error


class TestGetProjectBuilds:
    """Tests for the get_project_builds tool function."""

    def test_get_builds_success(self, fake_api_active):
        """get_project_builds returns builds for a project."""
        result = get_project_builds("proj_001")

        assert result.success is True
        assert result.total == 1  # Arduino Shield has 1 build

    def test_get_builds_empty(self, fake_api_active):
        """get_project_builds handles projects with no builds."""
        result = get_project_builds("proj_002")

        assert result.success is True
        assert result.total == 0

    def test_get_builds_missing_id(self, fake_api_active):
        """get_project_builds returns error for missing project_id."""
        result = get_project_builds("")

        assert result.success is False
        assert "project_id is required" in result.error


class TestGetBuild:
    """Tests for the get_build tool function."""

    def test_get_build_success(self, fake_api_active):
        """get_build returns the correct build."""
        result = get_build("build_001")

        assert result.success is True
        assert result.data is not None
        assert result.data["build/id"] == "build_001"

    def test_get_build_not_found(self, fake_api_active):
        """get_build returns error for non-existent build."""
        result = get_build("nonexistent_build")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_get_build_empty_id(self, fake_api_active):
        """get_build returns error for empty build_id."""
        result = get_build("")

        assert result.success is False
        assert "build_id is required" in result.error


class TestUpdateBuild:
    """Tests for the update_build tool function."""

    def test_update_build_success(self, fake_api_active):
        """update_build successfully updates a build."""
        result = update_build("build_001", comments="Updated comment")

        assert result.success is True

    def test_update_build_missing_id(self, fake_api_active):
        """update_build returns error for missing build_id."""
        result = update_build("")

        assert result.success is False
        assert "build_id is required" in result.error
