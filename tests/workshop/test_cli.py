from pathlib import Path
import subprocess
import sys

import yaml


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[2]
)


def run_cli(
    *args: str,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "workshop_tools.cli",
            *args,
        ],
        cwd=(
            cwd
            if cwd is not None
            else REPOSITORY_ROOT
        ),
        text=True,
        capture_output=True,
    )


def test_help_exposes_foundation_domains() -> None:
    result = run_cli(
        "--help"
    )

    assert result.returncode == 0

    assert "authority" in result.stdout
    assert "coverage" in result.stdout
    assert "settings" in result.stdout


def test_coverage_check_passes_repository_state() -> None:
    result = run_cli(
        "coverage",
        "check",
    )

    assert result.returncode == 0, (
        result.stdout
        + result.stderr
    )

    assert (
        "COVERAGE=PASS"
        in result.stdout
    )


def test_coverage_check_works_outside_repository_root(
    tmp_path: Path,
) -> None:
    result = run_cli(
        "coverage",
        "check",
        cwd=tmp_path,
    )

    assert result.returncode == 0, (
        result.stdout
        + result.stderr
    )

    assert (
        "COVERAGE=PASS"
        in result.stdout
    )


def test_settings_resolve_respects_file_order(
    tmp_path: Path,
) -> None:
    global_file = (
        tmp_path
        / "global.yaml"
    )

    workspace_file = (
        tmp_path
        / "workspace.yaml"
    )

    user_file = (
        tmp_path
        / "user.yaml"
    )

    global_file.write_text(
        """
runtime:
  provider: mlx
  temperature: 0.1
tools:
  mcp: false
  shell: false
"""
    )

    workspace_file.write_text(
        """
runtime:
  provider: ollama
tools:
  mcp: true
"""
    )

    user_file.write_text(
        """
runtime:
  temperature: 0.7
"""
    )

    result = run_cli(
        "settings",
        "resolve",
        str(global_file),
        str(workspace_file),
        str(user_file),
        cwd=tmp_path,
    )

    assert result.returncode == 0, (
        result.stdout
        + result.stderr
    )

    resolved = yaml.safe_load(
        result.stdout
    )

    assert resolved == {
        "runtime": {
            "provider": "ollama",
            "temperature": 0.7,
        },
        "tools": {
            "mcp": True,
            "shell": False,
        },
    }


def test_settings_resolve_replaces_lists(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"

    first.write_text(
        """
tools:
  enabled:
    - a
    - b
"""
    )

    second.write_text(
        """
tools:
  enabled:
    - c
"""
    )

    result = run_cli(
        "settings",
        "resolve",
        str(first),
        str(second),
        cwd=tmp_path,
    )

    assert result.returncode == 0

    resolved = yaml.safe_load(
        result.stdout
    )

    assert resolved[
        "tools"
    ][
        "enabled"
    ] == [
        "c",
    ]


def test_missing_required_command_is_nonzero() -> None:
    result = run_cli()

    assert result.returncode != 0
