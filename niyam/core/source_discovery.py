"""Read-only source-control repository discovery."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from niyam.core.applications import register_application
from niyam.core.graph import link_objects


FetchJSON = Callable[[str, dict[str, str]], tuple[object, dict[str, str]]]
AI_MARKERS = re.compile(r"(^|[^a-z0-9])(ai|llm|agent|rag|copilot|model)([^a-z0-9]|$)")


class DiscoveredRepository(BaseModel):
    """Provider-neutral repository metadata."""

    provider: str
    external_id: str
    name: str
    full_name: str
    url: str
    owner: str
    default_branch: str | None = None
    private: bool = False
    archived: bool = False
    description: str | None = None
    topics: list[str] = Field(default_factory=list)
    ai_candidate: bool = False


class SourceDiscoveryResult(BaseModel):
    """Versioned provenance artifact for one provider scope."""

    schema_version: str = "1.0.0"
    provider: str
    scope: str
    collected_at: str
    repositories: list[DiscoveredRepository] = Field(default_factory=list)


def _default_fetch(url: str, headers: dict[str, str]) -> tuple[object, dict[str, str]]:
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=30) as response:
        payload = response.read(10_000_001)
        if len(payload) > 10_000_000:
            raise ValueError("Source discovery response exceeds 10 MB.")
        return json.loads(payload), {
            key.lower(): value for key, value in response.headers.items()
        }


def _is_ai_candidate(name: str, description: str | None, topics: list[str]) -> bool:
    text = " ".join([name, description or "", *topics]).lower()
    return bool(AI_MARKERS.search(text))


def _normalize_github(item: dict[str, Any]) -> DiscoveredRepository:
    topics = [str(topic) for topic in item.get("topics") or []]
    description = item.get("description")
    return DiscoveredRepository(
        provider="github",
        external_id=str(item["id"]),
        name=item["name"],
        full_name=item.get("full_name") or item["name"],
        url=item.get("html_url") or item.get("clone_url") or "",
        owner=(item.get("owner") or {}).get("login", ""),
        default_branch=item.get("default_branch"),
        private=bool(item.get("private", False)),
        archived=bool(item.get("archived", False)),
        description=description,
        topics=topics,
        ai_candidate=_is_ai_candidate(item["name"], description, topics),
    )


def _normalize_gitlab(item: dict[str, Any]) -> DiscoveredRepository:
    topics = [str(topic) for topic in item.get("topics") or item.get("tag_list") or []]
    description = item.get("description")
    return DiscoveredRepository(
        provider="gitlab",
        external_id=str(item["id"]),
        name=item["name"],
        full_name=item.get("path_with_namespace") or item["name"],
        url=item.get("web_url") or "",
        owner=(item.get("namespace") or {}).get("full_path", ""),
        default_branch=item.get("default_branch"),
        private=item.get("visibility") == "private",
        archived=bool(item.get("archived", False)),
        description=description,
        topics=topics,
        ai_candidate=_is_ai_candidate(item["name"], description, topics),
    )


def _normalize_azure(item: dict[str, Any]) -> DiscoveredRepository:
    project = (item.get("project") or {}).get("name", "")
    name = item["name"]
    return DiscoveredRepository(
        provider="azure-devops",
        external_id=str(item["id"]),
        name=name,
        full_name=f"{project}/{name}" if project else name,
        url=item.get("webUrl") or item.get("remoteUrl") or "",
        owner=project,
        default_branch=(item.get("defaultBranch") or "").removeprefix("refs/heads/")
        or None,
        archived=bool(item.get("isDisabled", False)),
        ai_candidate=_is_ai_candidate(name, None, []),
    )


def discover_source_repositories(
    provider: str,
    organization: str,
    *,
    project: str | None = None,
    token: str | None = None,
    base_url: str | None = None,
    fetcher: FetchJSON | None = None,
    max_pages: int = 10,
) -> SourceDiscoveryResult:
    """List repository metadata using a provider's read-only REST endpoint."""
    if provider not in {"github", "gitlab", "azure-devops"}:
        raise ValueError("Provider must be github, gitlab, or azure-devops.")
    if not 1 <= max_pages <= 100:
        raise ValueError("max_pages must be between 1 and 100.")
    fetch = fetcher or _default_fetch
    headers = {"User-Agent": "niyam/1.0"}
    repositories: list[DiscoveredRepository] = []

    if provider == "github":
        base = (base_url or "https://api.github.com").rstrip("/")
        headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        if token:
            headers["Authorization"] = f"Bearer {token}"
        for page in range(1, max_pages + 1):
            query = urlencode({"type": "all", "per_page": 100, "page": page})
            payload, _ = fetch(
                f"{base}/orgs/{quote(organization, safe='')}/repos?{query}", headers
            )
            items = payload if isinstance(payload, list) else []
            repositories.extend(_normalize_github(item) for item in items)
            if len(items) < 100:
                break

    elif provider == "gitlab":
        base = (base_url or "https://gitlab.com/api/v4").rstrip("/")
        if token:
            headers["PRIVATE-TOKEN"] = token
        for page in range(1, max_pages + 1):
            query = urlencode(
                {"include_subgroups": "true", "per_page": 100, "page": page}
            )
            payload, _ = fetch(
                f"{base}/groups/{quote(organization, safe='')}/projects?{query}",
                headers,
            )
            items = payload if isinstance(payload, list) else []
            repositories.extend(_normalize_gitlab(item) for item in items)
            if len(items) < 100:
                break

    else:
        base = (base_url or "https://dev.azure.com").rstrip("/")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        project_path = f"/{quote(project, safe='')}" if project else ""
        query = urlencode({"api-version": "7.1"})
        payload, _ = fetch(
            f"{base}/{quote(organization, safe='')}{project_path}/_apis/git/repositories?{query}",
            headers,
        )
        items = payload.get("value", []) if isinstance(payload, dict) else []
        repositories.extend(_normalize_azure(item) for item in items)

    repositories.sort(key=lambda item: (item.full_name.lower(), item.external_id))
    return SourceDiscoveryResult(
        provider=provider,
        scope=f"{organization}/{project}" if project else organization,
        collected_at=datetime.now(timezone.utc).isoformat(),
        repositories=repositories,
    )


def _application_id(repository: DiscoveredRepository) -> str:
    value = f"{repository.provider}-{repository.full_name}".lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def register_discovered_applications(
    result: SourceDiscoveryResult,
    root: Path,
    *,
    register_all: bool = False,
) -> list[str]:
    """Idempotently register detected AI repositories as Applications."""
    registered = []
    for repository in result.repositories:
        if not register_all and not repository.ai_candidate:
            continue
        application_id = _application_id(repository)
        register_application(
            application_id,
            name=repository.name,
            owner=repository.owner or None,
            repository=repository.url,
            description=repository.description,
            tags=sorted({result.provider, "discovered", *repository.topics}),
            update=True,
            root=root,
        )
        link_objects(
            "application",
            application_id,
            "has_repository",
            "repository",
            repository.full_name,
            root=root,
        )
        registered.append(application_id)
    return registered


def save_source_discovery(result: SourceDiscoveryResult, root: Path) -> Path:
    """Persist normalized discovery evidence without credentials."""
    directory = root / ".niyam" / "discovery"
    directory.mkdir(parents=True, exist_ok=True)
    scope = re.sub(r"[^a-zA-Z0-9._-]+", "-", result.scope).strip("-")
    path = directory / f"{result.provider}-{scope}.json"
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    temporary.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return path
