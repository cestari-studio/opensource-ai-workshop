from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path


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
