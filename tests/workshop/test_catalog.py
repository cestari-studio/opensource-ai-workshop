from pathlib import Path

from workshop_tools.catalog import discover_source


def test_discovery_is_sorted_and_classifies_files(
    tmp_path: Path,
) -> None:
    (tmp_path / "mellea").mkdir()
    (tmp_path / "docs" / "examples").mkdir(parents=True)
    (tmp_path / "test").mkdir()
    (tmp_path / ".git").mkdir()

    (tmp_path / "mellea" / "session.py").write_text(
        "x = 1\n"
    )
    (tmp_path / "docs" / "guide.md").write_text(
        "# guide\n"
    )
    (
        tmp_path
        / "docs"
        / "examples"
        / "demo.py"
    ).write_text(
        "print('x')\n"
    )
    (
        tmp_path
        / "test"
        / "test_session.py"
    ).write_text(
        "def test_x(): pass\n"
    )
    (
        tmp_path
        / ".git"
        / "config"
    ).write_text(
        "ignored\n"
    )

    rows = discover_source(tmp_path)

    assert [row.path for row in rows] == sorted(
        row.path for row in rows
    )

    assert [row.kind for row in rows] == [
        "example",
        "documentation",
        "source",
        "test",
    ]

    assert all(
        len(row.sha256) == 64
        for row in rows
    )

    assert not any(
        row.path.startswith(".git/")
        for row in rows
    )


def test_discovery_hash_changes_when_content_changes(
    tmp_path: Path,
) -> None:
    (tmp_path / "mellea").mkdir()

    path = tmp_path / "mellea" / "a.py"
    path.write_text("a\n")

    first = discover_source(tmp_path)[0].sha256

    path.write_text("b\n")

    second = discover_source(tmp_path)[0].sha256

    assert first != second


def test_discovery_excludes_generated_and_model_artifacts(
    tmp_path: Path,
) -> None:
    (tmp_path / "mellea").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "__pycache__").mkdir()

    (tmp_path / "mellea" / "valid.py").write_text(
        "x = 1\n"
    )
    (tmp_path / ".venv" / "ignored.py").write_text(
        "ignored\n"
    )
    (
        tmp_path
        / "__pycache__"
        / "ignored.pyc"
    ).write_bytes(b"ignored")

    (tmp_path / "weights.gguf").write_bytes(
        b"model"
    )
    (tmp_path / "weights.safetensors").write_bytes(
        b"model"
    )

    rows = discover_source(tmp_path)

    assert [row.path for row in rows] == [
        "mellea/valid.py"
    ]
