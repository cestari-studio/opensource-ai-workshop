from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml


EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}

EXCLUDED_SUFFIXES = {
    ".gguf",
    ".safetensors",
    ".bin",
    ".pt",
    ".pth",
    ".pyc",
}


@dataclass(frozen=True)
class SourceEntry:
    path: str
    kind: str
    sha256: str


def classify(path: str) -> str:
    if path.startswith("docs/examples/"):
        return "example"

    if path.startswith("docs/"):
        return "documentation"

    if (
        path.startswith("test/")
        or path.startswith("tests/")
    ):
        return "test"

    if (
        path.startswith("mellea/")
        or path.startswith("cli/")
    ):
        return "source"

    return "engineering"


def discover_source(
    checkout: Path,
) -> list[SourceEntry]:
    rows: list[SourceEntry] = []

    for root, dirnames, filenames in os.walk(checkout):
        dirnames[:] = sorted(
            dirname
            for dirname in dirnames
            if dirname not in EXCLUDED_DIRS
        )

        root_path = Path(root)

        for filename in sorted(filenames):
            path = root_path / filename

            if path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue

            rel = path.relative_to(checkout)
            rel_posix = rel.as_posix()

            rows.append(
                SourceEntry(
                    path=rel_posix,
                    kind=classify(rel_posix),
                    sha256=hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest(),
                )
            )

    return sorted(
        rows,
        key=lambda row: row.path,
    )


def write_source_manifest(
    entries: list[SourceEntry],
    output: Path,
    revision: str,
) -> None:
    payload = {
        "schemaVersion": "1.0.0",
        "revision": revision,
        "entries": [
            asdict(entry)
            for entry in entries
        ],
    }

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )



@dataclass(frozen=True)
class Capability:
    id: str
    domain: str
    status: str
    source_paths: tuple[str, ...]
    surfaces: tuple[str, ...]
    evidence: dict[str, bool]
    authorization_permission: str | None


def load_capability_catalog(
    path: Path,
) -> list[Capability]:
    raw: dict[str, Any] = (
        yaml.safe_load(path.read_text())
        or {}
    )

    result: list[Capability] = []

    for row in raw.get(
        "capabilities",
        [],
    ):
        authorization = (
            row.get("authorization")
            or {}
        )

        result.append(
            Capability(
                id=str(row["id"]),
                domain=str(row["domain"]),
                status=str(row["status"]),
                source_paths=tuple(
                    str(value)
                    for value
                    in row.get(
                        "source_paths",
                        [],
                    )
                ),
                surfaces=tuple(
                    str(value)
                    for value
                    in row.get(
                        "surfaces",
                        [],
                    )
                ),
                evidence={
                    str(key): bool(value)
                    for key, value
                    in (
                        row.get("evidence")
                        or {}
                    ).items()
                },
                authorization_permission=(
                    str(
                        authorization[
                            "permission"
                        ]
                    )
                    if authorization.get(
                        "permission"
                    )
                    is not None
                    else None
                ),
            )
        )

    return result


def validate_capability_catalog(
    capabilities: list[Capability],
    source_paths: set[str],
) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()

    public_surfaces = {
        "api",
        "cli",
        "computer",
        "openwebui",
    }

    for capability in capabilities:
        if capability.id in seen:
            errors.append(
                f"{capability.id}: "
                "duplicate capability id"
            )

        seen.add(capability.id)

        for source_path in (
            capability.source_paths
        ):
            if source_path not in source_paths:
                errors.append(
                    f"{capability.id}: "
                    "unknown source path "
                    f"{source_path}"
                )

        if (
            public_surfaces.intersection(
                capability.surfaces
            )
            and not (
                capability
                .authorization_permission
            )
        ):
            errors.append(
                f"{capability.id}: "
                "public surface requires "
                "authorization.permission"
            )

    return errors
