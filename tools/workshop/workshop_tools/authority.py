from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class RepositoryLock:
    repository: str
    remote: str
    revision: str
    mode: str
    required_clean_worktree: bool


@dataclass(frozen=True)
class CheckoutAttestation:
    expected_revision: str
    actual_revision: str
    expected_tree: str
    actual_tree: str
    clean: bool
    ok: bool


def _git(checkout: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=checkout,
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def load_repository_lock(
    path: Path,
) -> RepositoryLock:
    data = json.loads(path.read_text())

    return RepositoryLock(
        repository=str(data["repository"]),
        remote=str(data["remote"]),
        revision=str(data["revision"]),
        mode=str(data["mode"]),
        required_clean_worktree=bool(
            data.get("requiredCleanWorktree", True)
        ),
    )


def attest_checkout(
    lock: RepositoryLock,
    checkout: Path,
) -> CheckoutAttestation:
    expected_revision = lock.revision

    actual_revision = _git(
        checkout,
        "rev-parse",
        "HEAD",
    )

    expected_tree = _git(
        checkout,
        "rev-parse",
        f"{expected_revision}^{{tree}}",
    )

    actual_tree = _git(
        checkout,
        "rev-parse",
        "HEAD^{tree}",
    )

    clean = (
        _git(
            checkout,
            "status",
            "--porcelain",
        )
        == ""
    )

    ok = (
        actual_revision == expected_revision
        and actual_tree == expected_tree
        and (
            clean
            or not lock.required_clean_worktree
        )
    )

    return CheckoutAttestation(
        expected_revision=expected_revision,
        actual_revision=actual_revision,
        expected_tree=expected_tree,
        actual_tree=actual_tree,
        clean=clean,
        ok=ok,
    )
