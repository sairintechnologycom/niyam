"""Read-only cloud and Kubernetes AI runtime discovery."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field

from niyam.core.applications import require_application
from niyam.core.graph import link_objects


CommandRunner = Callable[[list[str]], object]
AssetType = Literal["model", "agent", "endpoint", "workload", "service"]


class RuntimeAsset(BaseModel):
    """Provider-neutral runtime asset metadata."""

    provider: str
    asset_type: AssetType
    external_id: str
    name: str
    location: str | None = None
    owner: str | None = None
    endpoint: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuntimeDiscoveryResult(BaseModel):
    """Versioned runtime discovery evidence."""

    schema_version: str = "1.0.0"
    provider: str
    scope: str
    collected_at: str
    assets: list[RuntimeAsset] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def _default_runner(command: list[str]) -> object:
    try:
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"{command[0]} unavailable or timed out") from exc
    if result.returncode != 0:
        raise RuntimeError(f"{command[0]} returned exit {result.returncode}")
    if len(result.stdout) > 10_000_000:
        raise RuntimeError(f"{command[0]} output exceeds 10 MB")
    try:
        return json.loads(result.stdout or "null")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{command[0]} returned invalid JSON") from exc


def _asset(
    provider: str,
    asset_type: AssetType,
    external_id: object,
    name: str,
    **values: Any,
) -> RuntimeAsset:
    return RuntimeAsset(
        provider=provider,
        asset_type=asset_type,
        external_id=str(external_id),
        name=name,
        **values,
    )


def _aws_models(payload: object, region: str | None) -> list[RuntimeAsset]:
    items = payload.get("modelSummaries", []) if isinstance(payload, dict) else []
    return [
        _asset(
            "aws",
            "model",
            item.get("modelArn") or item.get("modelId"),
            item.get("modelName") or item.get("modelId", "model"),
            location=region,
            owner=item.get("providerName"),
            metadata={"model_id": item.get("modelId", "")},
        )
        for item in items
    ]


def _aws_agents(payload: object, region: str | None) -> list[RuntimeAsset]:
    items = payload.get("agentSummaries", []) if isinstance(payload, dict) else []
    return [
        _asset(
            "aws",
            "agent",
            item.get("agentArn") or item.get("agentId"),
            item.get("agentName") or item.get("agentId", "agent"),
            location=region,
            status=item.get("agentStatus"),
            metadata={"version": str(item.get("latestAgentVersion", ""))},
        )
        for item in items
    ]


def _aws_endpoints(payload: object, region: str | None) -> list[RuntimeAsset]:
    items = payload.get("Endpoints", []) if isinstance(payload, dict) else []
    return [
        _asset(
            "aws",
            "endpoint",
            item.get("EndpointArn") or item.get("EndpointName"),
            item.get("EndpointName", "endpoint"),
            location=region,
            status=item.get("EndpointStatus"),
        )
        for item in items
    ]


def _azure_services(payload: object) -> list[RuntimeAsset]:
    items = payload if isinstance(payload, list) else []
    return [
        _asset(
            "azure",
            "service",
            item.get("id") or item.get("name"),
            item.get("name", "cognitive-service"),
            location=item.get("location"),
            owner=item.get("resourceGroup"),
            endpoint=(item.get("properties") or {}).get("endpoint"),
            metadata={"kind": item.get("kind", "")},
        )
        for item in items
    ]


def _azure_endpoints(payload: object, owner: str | None) -> list[RuntimeAsset]:
    items = payload if isinstance(payload, list) else []
    return [
        _asset(
            "azure",
            "endpoint",
            item.get("id") or item.get("name"),
            item.get("name", "endpoint"),
            location=item.get("location"),
            owner=owner,
            endpoint=item.get("scoring_uri"),
            status=item.get("provisioning_state"),
        )
        for item in items
    ]


def _gcp_assets(
    payload: object, asset_type: Literal["model", "endpoint"], region: str | None
) -> list[RuntimeAsset]:
    items = payload if isinstance(payload, list) else []
    assets = []
    for item in items:
        full_name = item.get("name", "")
        labels = item.get("labels") or {}
        assets.append(
            _asset(
                "gcp",
                asset_type,
                full_name.rsplit("/", 1)[-1] or full_name,
                item.get("displayName") or full_name.rsplit("/", 1)[-1],
                location=region,
                owner=labels.get("owner") or labels.get("team"),
                metadata={"resource_name": full_name},
            )
        )
    return assets


def _kubernetes_assets(payload: object) -> list[RuntimeAsset]:
    items = payload.get("items", []) if isinstance(payload, dict) else []
    assets = []
    for item in items:
        kind = item.get("kind", "")
        metadata = item.get("metadata") or {}
        spec = item.get("spec") or {}
        namespace = metadata.get("namespace", "default")
        labels = metadata.get("labels") or {}
        name = metadata.get("name", "resource")
        if kind.lower() == "service":
            asset_type: AssetType = "service"
            endpoint = spec.get("externalName") or spec.get("clusterIP")
            images: list[str] = []
        else:
            text = f"{name} {json.dumps(labels)}".lower()
            asset_type = (
                "agent"
                if re.search(r"(^|[^a-z0-9])(ai|llm|agent|rag)([^a-z0-9]|$)", text)
                else "workload"
            )
            endpoint = None
            pod_spec = (spec.get("template") or {}).get("spec") or {}
            images = [
                container.get("image", "")
                for container in pod_spec.get("containers", [])
                if container.get("image")
            ]
        assets.append(
            _asset(
                "kubernetes",
                asset_type,
                metadata.get("uid") or f"{namespace}/{kind}/{name}",
                name,
                location=namespace,
                owner=labels.get("owner") or labels.get("team"),
                endpoint=endpoint,
                status=str((item.get("status") or {}).get("readyReplicas", "")) or None,
                metadata={"kind": kind, "images": images},
            )
        )
    return assets


def discover_runtime_assets(
    provider: str,
    *,
    runner: CommandRunner | None = None,
    region: str | None = None,
    project: str | None = None,
    resource_group: str | None = None,
    workspace: str | None = None,
    subscription: str | None = None,
    context: str | None = None,
) -> RuntimeDiscoveryResult:
    """Run fixed provider list commands and normalize their JSON output."""
    if provider not in {"aws", "azure", "gcp", "kubernetes"}:
        raise ValueError("Provider must be aws, azure, gcp, or kubernetes.")
    run = runner or _default_runner
    assets: list[RuntimeAsset] = []
    errors: list[str] = []

    def collect(
        command: list[str], normalizer: Callable[[object], list[RuntimeAsset]]
    ) -> None:
        try:
            assets.extend(normalizer(run(command)))
        except Exception as exc:
            label = " ".join(command[:3])
            errors.append(f"{label}: {type(exc).__name__}")

    if provider == "aws":
        suffix = ["--output", "json"] + (["--region", region] if region else [])
        collect(
            ["aws", "bedrock", "list-foundation-models", *suffix],
            lambda payload: _aws_models(payload, region),
        )
        collect(
            ["aws", "bedrock-agent", "list-agents", *suffix],
            lambda payload: _aws_agents(payload, region),
        )
        collect(
            ["aws", "sagemaker", "list-endpoints", *suffix],
            lambda payload: _aws_endpoints(payload, region),
        )
        scope = region or "default"
    elif provider == "azure":
        suffix = ["--subscription", subscription] if subscription else []
        collect(
            ["az", "cognitiveservices", "account", "list", "--output", "json", *suffix],
            _azure_services,
        )
        if resource_group and workspace:
            collect(
                [
                    "az",
                    "ml",
                    "online-endpoint",
                    "list",
                    "--resource-group",
                    resource_group,
                    "--workspace-name",
                    workspace,
                    "--output",
                    "json",
                    *suffix,
                ],
                lambda payload: _azure_endpoints(payload, resource_group),
            )
        scope = (
            "/".join(filter(None, [subscription, resource_group, workspace]))
            or "default"
        )
    elif provider == "gcp":
        if not project or not region:
            raise ValueError("GCP discovery requires project and region.")
        suffix = ["--project", project, "--region", region, "--format", "json"]
        collect(
            ["gcloud", "ai", "models", "list", *suffix],
            lambda payload: _gcp_assets(payload, "model", region),
        )
        collect(
            ["gcloud", "ai", "endpoints", "list", *suffix],
            lambda payload: _gcp_assets(payload, "endpoint", region),
        )
        scope = f"{project}/{region}"
    else:
        command = [
            "kubectl",
            "get",
            "deployments,statefulsets,services",
            "--all-namespaces",
            "--output",
            "json",
        ]
        if context:
            command.extend(["--context", context])
        collect(command, _kubernetes_assets)
        scope = context or "current-context"

    assets.sort(
        key=lambda asset: (asset.asset_type, asset.name.lower(), asset.external_id)
    )
    return RuntimeDiscoveryResult(
        provider=provider,
        scope=scope,
        collected_at=datetime.now(timezone.utc).isoformat(),
        assets=assets,
        errors=errors,
    )


def register_runtime_assets(
    result: RuntimeDiscoveryResult,
    application_id: str,
    root: Path,
) -> int:
    """Link discovered runtime assets to a registered Application."""
    require_application(application_id, root)
    for asset in result.assets:
        link_objects(
            "application",
            application_id,
            "uses",
            asset.asset_type,
            f"{asset.provider}:{asset.external_id}",
            root=root,
        )
    return len(result.assets)


def save_runtime_discovery(result: RuntimeDiscoveryResult, root: Path) -> Path:
    """Persist normalized runtime discovery evidence."""
    directory = root / ".niyam" / "discovery"
    directory.mkdir(parents=True, exist_ok=True)
    scope = re.sub(r"[^a-zA-Z0-9._-]+", "-", result.scope).strip("-")
    path = directory / f"runtime-{result.provider}-{scope}.json"
    temporary = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    temporary.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return path
