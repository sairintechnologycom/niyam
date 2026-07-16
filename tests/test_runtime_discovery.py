"""Tests for read-only cloud and Kubernetes runtime discovery."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from niyam.cli import app
from niyam.core.applications import register_application
from niyam.core.graph import get_relationships
from niyam.core.runtime_discovery import (
    RuntimeAsset,
    RuntimeDiscoveryResult,
    discover_runtime_assets,
    register_runtime_assets,
)


@pytest.mark.parametrize(
    ("provider", "kwargs", "responses", "expected_types"),
    [
        (
            "aws",
            {"region": "us-east-1"},
            {
                "bedrock": {
                    "modelSummaries": [
                        {
                            "modelId": "anthropic.claude",
                            "modelName": "Claude",
                            "providerName": "Anthropic",
                            "modelArn": "arn:model",
                        }
                    ]
                },
                "bedrock-agent": {
                    "agentSummaries": [
                        {
                            "agentId": "A1",
                            "agentName": "support-agent",
                            "agentArn": "arn:agent",
                            "agentStatus": "PREPARED",
                        }
                    ]
                },
                "sagemaker": {
                    "Endpoints": [
                        {
                            "EndpointName": "support-endpoint",
                            "EndpointArn": "arn:endpoint",
                            "EndpointStatus": "InService",
                        }
                    ]
                },
            },
            {"model", "agent", "endpoint"},
        ),
        (
            "azure",
            {"resource_group": "rg", "workspace": "ml"},
            {
                "cognitiveservices": [
                    {
                        "id": "/subscriptions/s1/accounts/openai",
                        "name": "openai",
                        "kind": "OpenAI",
                        "location": "eastus",
                        "resourceGroup": "rg",
                        "properties": {"endpoint": "https://openai.example"},
                    }
                ],
                "ml": [
                    {
                        "id": "/subscriptions/s1/endpoints/chat",
                        "name": "chat",
                        "location": "eastus",
                        "scoring_uri": "https://chat.example/score",
                        "provisioning_state": "Succeeded",
                    }
                ],
            },
            {"service", "endpoint"},
        ),
        (
            "gcp",
            {"project": "p1", "region": "us-central1"},
            {
                "models": [
                    {
                        "name": "projects/p1/locations/us-central1/models/123",
                        "displayName": "support-model",
                        "labels": {"owner": "ml-team"},
                    }
                ],
                "endpoints": [
                    {
                        "name": "projects/p1/locations/us-central1/endpoints/456",
                        "displayName": "support-endpoint",
                        "labels": {"owner": "ml-team"},
                    }
                ],
            },
            {"model", "endpoint"},
        ),
        (
            "kubernetes",
            {"context": "dev"},
            {
                "kubectl": {
                    "items": [
                        {
                            "kind": "Deployment",
                            "metadata": {
                                "uid": "u1",
                                "name": "support-agent",
                                "namespace": "ai",
                                "labels": {"owner": "platform"},
                            },
                            "spec": {
                                "template": {
                                    "spec": {
                                        "containers": [
                                            {"image": "acme/support-agent:v1"}
                                        ]
                                    }
                                }
                            },
                            "status": {"readyReplicas": 1},
                        },
                        {
                            "kind": "Service",
                            "metadata": {
                                "uid": "u2",
                                "name": "support-api",
                                "namespace": "ai",
                            },
                            "spec": {"clusterIP": "10.0.0.1"},
                        },
                    ]
                }
            },
            {"agent", "service"},
        ),
    ],
)
def test_runtime_provider_payloads_normalize(
    provider: str,
    kwargs: dict,
    responses: dict,
    expected_types: set[str],
) -> None:
    commands: list[list[str]] = []

    def runner(command: list[str]):
        commands.append(command)
        joined = " ".join(command)
        return next(
            value
            for key, value in sorted(
                responses.items(), key=lambda item: len(item[0]), reverse=True
            )
            if key in joined
        )

    result = discover_runtime_assets(provider, runner=runner, **kwargs)

    assert {asset.asset_type for asset in result.assets} == expected_types
    assert result.errors == []
    assert commands
    assert all(
        "delete" not in command and "create" not in command for command in commands
    )


def test_runtime_discovery_keeps_partial_failures_visible() -> None:
    def runner(command: list[str]):
        if "bedrock-agent" in command:
            raise RuntimeError("access denied")
        return {}

    result = discover_runtime_assets("aws", runner=runner, region="us-east-1")

    assert len(result.errors) == 1
    assert "bedrock-agent" in result.errors[0]


def test_runtime_assets_link_to_registered_application(tmp_path: Path) -> None:
    register_application("support-bot", name="Support Bot", root=tmp_path)
    result = RuntimeDiscoveryResult(
        provider="aws",
        scope="us-east-1",
        collected_at="2026-07-14T00:00:00Z",
        assets=[
            RuntimeAsset(
                provider="aws",
                asset_type="model",
                external_id="m1",
                name="Model One",
            )
        ],
    )

    assert register_runtime_assets(result, "support-bot", tmp_path) == 1
    assert register_runtime_assets(result, "support-bot", tmp_path) == 1
    edges = get_relationships("application", "support-bot", root=tmp_path)
    assert len(edges) == 1
    assert edges[0].target_id == "aws:m1"


def test_runtime_discovery_cli_persists_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".niyam").mkdir()
    result = RuntimeDiscoveryResult(
        provider="gcp",
        scope="p1/us-central1",
        collected_at="2026-07-14T00:00:00Z",
    )
    monkeypatch.setattr(
        "niyam.cli.discovery.discover_runtime_assets",
        lambda *args, **kwargs: result,
    )

    output = CliRunner().invoke(
        app,
        [
            "discovery",
            "runtime",
            "--provider",
            "gcp",
            "--project",
            "p1",
            "--region",
            "us-central1",
        ],
    )

    assert output.exit_code == 0, output.stdout
    artifact = tmp_path / ".niyam" / "discovery" / "runtime-gcp-p1-us-central1.json"
    assert json.loads(artifact.read_text())["provider"] == "gcp"
