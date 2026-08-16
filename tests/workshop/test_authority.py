from pathlib import Path
import subprocess

from workshop_tools.authority import (
    attest_checkout,
    load_repository_lock,
)


def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=cwd,
        text=True,
    ).strip()


def initialize_repo(repo: Path) -> str:
    repo.mkdir()

    subprocess.run(
        ["git", "init", "-q"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Workshop Test"],
        cwd=repo,
        check=True,
    )

    (repo / "a.txt").write_text("a\n")

    subprocess.run(
        ["git", "add", "a.txt"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-qm", "init"],
        cwd=repo,
        check=True,
    )

    return git("rev-parse", "HEAD", cwd=repo)


def write_lock(path: Path, sha: str) -> None:
    path.write_text(
        "{"
        '"schemaVersion":"1.0.0",'
        '"repository":"test/repo",'
        '"remote":"local",'
        f'"revision":"{sha}",'
        '"mode":"read_only",'
        '"requiredCleanWorktree":true'
        "}"
    )


def test_load_mellea_lock() -> None:
    lock = load_repository_lock(
        Path("authority/mellea/upstream.lock.json")
    )

    assert lock.repository == "generative-computing/mellea"
    assert (
        lock.revision
        == "853b04fe572b3f8d2947c56750c883aeae12ea0b"
    )
    assert lock.mode == "read_only"
    assert lock.required_clean_worktree is True


def test_attest_checkout_accepts_exact_clean_checkout(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    sha = initialize_repo(repo)

    lock_path = tmp_path / "lock.json"
    write_lock(lock_path, sha)

    result = attest_checkout(
        load_repository_lock(lock_path),
        repo,
    )

    assert result.ok is True
    assert result.actual_revision == sha
    assert result.clean is True


def test_attest_checkout_rejects_dirty_checkout(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    sha = initialize_repo(repo)

    (repo / "a.txt").write_text("dirty\n")

    lock_path = tmp_path / "lock.json"
    write_lock(lock_path, sha)

    result = attest_checkout(
        load_repository_lock(lock_path),
        repo,
    )

    assert result.ok is False
    assert result.clean is False
