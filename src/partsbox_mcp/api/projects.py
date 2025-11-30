"""
Projects API module.

Provides MCP tools for project/BOM management:
- project/all - List all projects
- project/get - Retrieve project details
- project/create - Create new project
- project/update - Modify project metadata
- project/delete - Remove project
- project/get-entries - Retrieve BOM entries
- project/add-entries - Insert BOM line items
- project/update-entries - Modify existing entries
- project/delete-entries - Remove entries
- project/get-builds - List all builds
- project/archive - Archive a project
- project/restore - Restore archived project
- build/get - Retrieve single build data
- build/update - Modify build comments
"""

from dataclasses import dataclass
from typing import Any

import requests

from partsbox_mcp.client import api_client, apply_query, cache


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class ProjectResponse:
    """Response for a single project."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class PaginatedProjectsResponse:
    """Response for paginated projects listing."""

    success: bool
    cache_key: str
    total: int
    offset: int
    limit: int
    has_more: bool
    data: list[Any]
    error: str | None = None
    query_applied: str | None = None


@dataclass
class ProjectOperationResponse:
    """Response for project modification operations."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class PaginatedEntriesResponse:
    """Response for paginated BOM entries."""

    success: bool
    cache_key: str
    total: int
    offset: int
    limit: int
    has_more: bool
    data: list[Any]
    error: str | None = None
    query_applied: str | None = None


@dataclass
class PaginatedBuildsResponse:
    """Response for paginated builds listing."""

    success: bool
    cache_key: str
    total: int
    offset: int
    limit: int
    has_more: bool
    data: list[Any]
    error: str | None = None
    query_applied: str | None = None


@dataclass
class BuildResponse:
    """Response for a single build."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


# =============================================================================
# Tool Functions
# =============================================================================


def list_projects(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
    include_archived: bool = False,
) -> PaginatedProjectsResponse:
    """
    List all projects with optional JMESPath query and pagination.

    Args:
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection. Examples:
            - "[?contains(\"project/name\", 'Arduino')]" - filter by name
            - "sort_by(@, &\"project/name\")" - sort by name
        include_archived: Include archived projects (default False)

    Returns:
        PaginatedProjectsResponse with projects data and pagination info
    """
    if limit < 1 or limit > 1000:
        return PaginatedProjectsResponse(
            success=False,
            error="limit must be between 1 and 1000",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if offset < 0:
        return PaginatedProjectsResponse(
            success=False,
            error="offset must be non-negative",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    try:
        if cache_key:
            entry = cache.get(cache_key)
            if entry:
                data = entry.data
                key = cache_key
            else:
                result = api_client._request("project/all")
                data = result.get("data", [])
                key = cache.create(data)
        else:
            result = api_client._request("project/all")
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedProjectsResponse(
            success=False,
            error=f"API request failed: {e}",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    # Filter out archived if not requested
    if not include_archived:
        data = [proj for proj in data if not proj.get("project/archived", False)]

    if query:
        result, error = apply_query(data, query)
        if error:
            return PaginatedProjectsResponse(
                success=False,
                error=error,
                cache_key=key,
                total=0,
                offset=0,
                limit=limit,
                has_more=False,
                query_applied=query,
                data=[],
            )
    else:
        result = data

    if not isinstance(result, list):
        return PaginatedProjectsResponse(
            success=True,
            cache_key=key,
            total=1,
            offset=0,
            limit=limit,
            has_more=False,
            query_applied=query,
            data=[result],
        )

    total = len(result)
    page = result[offset : offset + limit]

    return PaginatedProjectsResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def get_project(project_id: str) -> ProjectResponse:
    """
    Get detailed information for a specific project.

    Args:
        project_id: The unique identifier of the project

    Returns:
        ProjectResponse with project data or error
    """
    if not project_id:
        return ProjectResponse(success=False, error="project_id is required")

    try:
        result = api_client._request("project/get", {"project/id": project_id})
        data = result.get("data")
        if data is None:
            return ProjectResponse(
                success=False, error=f"Project not found: {project_id}"
            )
        return ProjectResponse(success=True, data=data)
    except requests.RequestException as e:
        return ProjectResponse(success=False, error=f"API request failed: {e}")


def create_project(
    name: str,
    description: str | None = None,
    comments: str | None = None,
    entries: list[dict[str, Any]] | None = None,
) -> ProjectOperationResponse:
    """
    Create a new project.

    Args:
        name: The project name
        description: Optional project description
        comments: Optional project comments
        entries: Optional list of initial BOM entries

    Returns:
        ProjectOperationResponse with the created project data
    """
    if not name:
        return ProjectOperationResponse(success=False, error="name is required")

    payload: dict[str, Any] = {"project/name": name}

    if description is not None:
        payload["project/description"] = description
    if comments is not None:
        payload["project/comments"] = comments
    if entries is not None:
        payload["project/entries"] = entries

    try:
        result = api_client._request("project/create", payload)
        return ProjectOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return ProjectOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def update_project(
    project_id: str,
    name: str | None = None,
    description: str | None = None,
    comments: str | None = None,
) -> ProjectOperationResponse:
    """
    Update project metadata.

    Args:
        project_id: The unique identifier of the project
        name: Optional new name
        description: Optional new description
        comments: Optional new comments

    Returns:
        ProjectOperationResponse with the updated project data
    """
    if not project_id:
        return ProjectOperationResponse(success=False, error="project_id is required")

    payload: dict[str, Any] = {"project/id": project_id}

    if name is not None:
        payload["project/name"] = name
    if description is not None:
        payload["project/description"] = description
    if comments is not None:
        payload["project/comments"] = comments

    try:
        result = api_client._request("project/update", payload)
        return ProjectOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return ProjectOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def delete_project(project_id: str) -> ProjectOperationResponse:
    """
    Delete a project.

    Args:
        project_id: The unique identifier of the project

    Returns:
        ProjectOperationResponse with the result
    """
    if not project_id:
        return ProjectOperationResponse(success=False, error="project_id is required")

    try:
        result = api_client._request("project/delete", {"project/id": project_id})
        return ProjectOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return ProjectOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def archive_project(project_id: str) -> ProjectOperationResponse:
    """
    Archive a project.

    Args:
        project_id: The unique identifier of the project

    Returns:
        ProjectOperationResponse with the result
    """
    if not project_id:
        return ProjectOperationResponse(success=False, error="project_id is required")

    try:
        result = api_client._request("project/archive", {"project/id": project_id})
        return ProjectOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return ProjectOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def restore_project(project_id: str) -> ProjectOperationResponse:
    """
    Restore an archived project.

    Args:
        project_id: The unique identifier of the project

    Returns:
        ProjectOperationResponse with the result
    """
    if not project_id:
        return ProjectOperationResponse(success=False, error="project_id is required")

    try:
        result = api_client._request("project/restore", {"project/id": project_id})
        return ProjectOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return ProjectOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def get_project_entries(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
    build_id: str | None = None,
) -> PaginatedEntriesResponse:
    """
    Get BOM entries for a project.

    Args:
        project_id: The project ID
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection
        build_id: Optional build ID for historical BOM snapshot

    Returns:
        PaginatedEntriesResponse with BOM entries and pagination info
    """
    if not project_id:
        return PaginatedEntriesResponse(
            success=False,
            error="project_id is required",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if limit < 1 or limit > 1000:
        return PaginatedEntriesResponse(
            success=False,
            error="limit must be between 1 and 1000",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if offset < 0:
        return PaginatedEntriesResponse(
            success=False,
            error="offset must be non-negative",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    try:
        if cache_key:
            entry = cache.get(cache_key)
            if entry:
                data = entry.data
                key = cache_key
            else:
                payload: dict[str, Any] = {"project/id": project_id}
                if build_id:
                    payload["build/id"] = build_id
                result = api_client._request("project/get-entries", payload)
                data = result.get("data", [])
                key = cache.create(data)
        else:
            payload = {"project/id": project_id}
            if build_id:
                payload["build/id"] = build_id
            result = api_client._request("project/get-entries", payload)
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedEntriesResponse(
            success=False,
            error=f"API request failed: {e}",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if query:
        result, error = apply_query(data, query)
        if error:
            return PaginatedEntriesResponse(
                success=False,
                error=error,
                cache_key=key,
                total=0,
                offset=0,
                limit=limit,
                has_more=False,
                query_applied=query,
                data=[],
            )
    else:
        result = data

    if not isinstance(result, list):
        return PaginatedEntriesResponse(
            success=True,
            cache_key=key,
            total=1,
            offset=0,
            limit=limit,
            has_more=False,
            query_applied=query,
            data=[result],
        )

    total = len(result)
    page = result[offset : offset + limit]

    return PaginatedEntriesResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def add_project_entries(
    project_id: str,
    entries: list[dict[str, Any]],
) -> ProjectOperationResponse:
    """
    Add BOM entries to a project.

    Args:
        project_id: The project ID
        entries: List of entry objects with required fields:
            - entry/part-id: The part ID
            - entry/quantity: Quantity per board
            - Optional: entry/designators, entry/comments

    Returns:
        ProjectOperationResponse with the result
    """
    if not project_id:
        return ProjectOperationResponse(success=False, error="project_id is required")
    if not entries:
        return ProjectOperationResponse(success=False, error="entries is required")

    payload: dict[str, Any] = {
        "project/id": project_id,
        "project/entries": entries,
    }

    try:
        result = api_client._request("project/add-entries", payload)
        return ProjectOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return ProjectOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def update_project_entries(
    project_id: str,
    entries: list[dict[str, Any]],
) -> ProjectOperationResponse:
    """
    Update existing BOM entries.

    Args:
        project_id: The project ID
        entries: List of entry objects with entry/id and fields to update

    Returns:
        ProjectOperationResponse with the result
    """
    if not project_id:
        return ProjectOperationResponse(success=False, error="project_id is required")
    if not entries:
        return ProjectOperationResponse(success=False, error="entries is required")

    payload: dict[str, Any] = {
        "project/id": project_id,
        "project/entries": entries,
    }

    try:
        result = api_client._request("project/update-entries", payload)
        return ProjectOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return ProjectOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def delete_project_entries(
    project_id: str,
    entry_ids: list[str],
) -> ProjectOperationResponse:
    """
    Delete BOM entries from a project.

    Args:
        project_id: The project ID
        entry_ids: List of entry IDs to delete

    Returns:
        ProjectOperationResponse with the result
    """
    if not project_id:
        return ProjectOperationResponse(success=False, error="project_id is required")
    if not entry_ids:
        return ProjectOperationResponse(success=False, error="entry_ids is required")

    payload: dict[str, Any] = {
        "project/id": project_id,
        "entry/ids": entry_ids,
    }

    try:
        result = api_client._request("project/delete-entries", payload)
        return ProjectOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return ProjectOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def get_project_builds(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> PaginatedBuildsResponse:
    """
    List all builds for a project.

    Args:
        project_id: The project ID
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection

    Returns:
        PaginatedBuildsResponse with builds data and pagination info
    """
    if not project_id:
        return PaginatedBuildsResponse(
            success=False,
            error="project_id is required",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if limit < 1 or limit > 1000:
        return PaginatedBuildsResponse(
            success=False,
            error="limit must be between 1 and 1000",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if offset < 0:
        return PaginatedBuildsResponse(
            success=False,
            error="offset must be non-negative",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    try:
        if cache_key:
            entry = cache.get(cache_key)
            if entry:
                data = entry.data
                key = cache_key
            else:
                result = api_client._request(
                    "project/get-builds", {"project/id": project_id}
                )
                data = result.get("data", [])
                key = cache.create(data)
        else:
            result = api_client._request(
                "project/get-builds", {"project/id": project_id}
            )
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedBuildsResponse(
            success=False,
            error=f"API request failed: {e}",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if query:
        result, error = apply_query(data, query)
        if error:
            return PaginatedBuildsResponse(
                success=False,
                error=error,
                cache_key=key,
                total=0,
                offset=0,
                limit=limit,
                has_more=False,
                query_applied=query,
                data=[],
            )
    else:
        result = data

    if not isinstance(result, list):
        return PaginatedBuildsResponse(
            success=True,
            cache_key=key,
            total=1,
            offset=0,
            limit=limit,
            has_more=False,
            query_applied=query,
            data=[result],
        )

    total = len(result)
    page = result[offset : offset + limit]

    return PaginatedBuildsResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def get_build(build_id: str) -> BuildResponse:
    """
    Get detailed information for a specific build.

    Args:
        build_id: The unique identifier of the build

    Returns:
        BuildResponse with build data or error
    """
    if not build_id:
        return BuildResponse(success=False, error="build_id is required")

    try:
        result = api_client._request("build/get", {"build/id": build_id})
        data = result.get("data")
        if data is None:
            return BuildResponse(success=False, error=f"Build not found: {build_id}")
        return BuildResponse(success=True, data=data)
    except requests.RequestException as e:
        return BuildResponse(success=False, error=f"API request failed: {e}")


def update_build(
    build_id: str,
    comments: str | None = None,
) -> BuildResponse:
    """
    Update build metadata.

    Args:
        build_id: The unique identifier of the build
        comments: Optional new comments

    Returns:
        BuildResponse with the updated build data
    """
    if not build_id:
        return BuildResponse(success=False, error="build_id is required")

    payload: dict[str, Any] = {"build/id": build_id}

    if comments is not None:
        payload["build/comments"] = comments

    try:
        result = api_client._request("build/update", payload)
        return BuildResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return BuildResponse(success=False, error=f"API request failed: {e}")
