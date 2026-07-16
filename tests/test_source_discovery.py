"""Tests for read-only source-control discovery."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.applications import load_application_registry
from niyam.core.graph import get_relationships
from niyam.core.source_discovery import (
    DiscoveredRepository,
    SourceDiscoveryResult,
    discover_source_repositories,
    register_discovered_applications,
)


@pytest.mark.parametrize(
    ("provider", "payload", "expected_name", "expected_url"),
    [
        (
            "github",
            [
                {
                    "id": 1,
                    "name": "support-agent",
                    "full_name": "acme/support-agent",
                    "html_url": "https://github.com/acme/support-agent",
                    "default_branch": "main",
                    "private": True,
                    "archived": False,
                    "owner": {"login": "acme"},
                    "topics": ["llm"],
                }
            ],
            "acme/support-agent",
            "https://api.github.com/orgs/acme/repos",
        ),
        (
            "gitlab",
            [
                {
                    "id": 2,
                    "name": "support-agent",
                    "path_with_namespace": "acme/support-agent",
                    "web_url": "https://gitlab.com/acme/support-agent",
                    "default_branch": "main",
                    "visibility": "private",
                    "archived": False,
                    "namespace": {"full_path": "acme"},
                    "topics": ["rag"],
                }
            ],
            "acme/support-agent",
            "https://gitlab.com/api/v4/groups/acme/projects",
        ),
        (
            "azure-devops",
            {
                "count": 1,
                "value": [
                    {
                        "id": "repo-3",
                        "name": "support-agent",
                        "webUrl": "https://dev.azure.com/acme/ai/_git/support-agent",
                        "defaultBranch": "refs/heads/main",
                        "isDisabled": False,
                        "project": {"name": "ai"},
                    }
                ],
            },
            "ai/support-agent",
            "https://dev.azure.com/acme/ai/_apis/git/repositories",
        ),
    ],
)
def test_provider_payloads_normalize_without_persisting_tokens(
    provider: str,
    payload: object,
    expected_name: str,
    expected_url: str,
) -> None:
    requests: list[tuple[str, dict[str, str]]] = []

    def fetch(url: str, headers: dict[str, str]):
        requests.append((url, headers))
        return payload, {}

    result = discover_source_repositories(
        provider,
        "acme",
        project="ai" if provider == "azure-devops" else None,
        token="TOP-SECRET",
        fetcher=fetch,
    )

    assert result.repositories[0].full_name == expected_name
    assert result.repositories[0].ai_candidate is True
    assert requests[0][0].startswith(expected_url)
    assert "TOP-SECRET" not in result.model_dump_json()


def test_detected_apps_register_idempotently_and_link_to_repositories(
    tmp_path: Path,
) -> None:
    result = SourceDiscoveryResult(
        provider="github",
        scope="acme",
        collected_at="2026-07-14T00:00:00Z",
        repositories=[
            DiscoveredRepository(
                provider="github",
                external_id="1",
                name="support-agent",
                full_name="acme/support-agent",
                url="https://github.com/acme/support-agent",
                owner="acme",
                ai_candidate=True,
                topics=["llm"],
            ),
            DiscoveredRepository(
                provider="github",
                external_id="2",
                name="website",
                full_name="acme/website",
                url="https://github.com/acme/website",
                owner="acme",
                ai_candidate=False,
            ),
        ],
    )

    first = register_discovered_applications(result, tmp_path)
    second = register_discovered_applications(result, tmp_path)

    assert first == second == ["github-acme-support-agent"]
    registry = load_application_registry(tmp_path)
    assert list(registry.applications) == ["github-acme-support-agent"]
    edges = get_relationships("application", "github-acme-support-agent", root=tmp_path)
    assert edges[0].target_id == "acme/support-agent"


def test_source_discovery_pagination_is_bounded() -> None:
    calls = 0
    page = [
        {
            "id": index,
            "name": f"repo-{index}",
            "full_name": f"acme/repo-{index}",
            "html_url": f"https://github.com/acme/repo-{index}",
            "owner": {"login": "acme"},
        }
        for index in range(100)
    ]

    def fetch(url: str, headers: dict[str, str]):
        nonlocal calls
        calls += 1
        return page, {}

    result = discover_source_repositories("github", "acme", fetcher=fetch, max_pages=2)

    assert calls == 2
    assert len(result.repositories) == 200


def test_source_discovery_cli_persists_normalized_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".niyam").mkdir()
    result = SourceDiscoveryResult(
        provider="github",
        scope="acme",
        collected_at="2026-07-14T00:00:00Z",
        repositories=[],
    )
    monkeypatch.setattr(
        "niyam.cli.discovery.discover_source_repositories",
        lambda *args, **kwargs: result,
    )

    output = CliRunner().invoke(
        app, ["discovery", "source", "--provider", "github", "--organization", "acme"]
    )

    assert output.exit_code == 0, output.stdout
    artifact = tmp_path / ".niyam" / "discovery" / "github-acme.json"
    assert json.loads(artifact.read_text())["provider"] == "github"
