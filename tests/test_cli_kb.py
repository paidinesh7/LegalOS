"""Tests for CLI kb command group using Click's test runner."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from legalos.cli import cli
from legalos.profile.schemas import (
    LearningCategory,
    LearningEntry,
    LearningsStore,
)
from legalos.profile.store import append_learning, load_learnings


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture
def legalos_dir(tmp_path: Path) -> Path:
    """Create a .legalos directory and patch _resolve_dir to use it."""
    d = tmp_path / ".legalos"
    d.mkdir()
    return d


def _patch_resolve(legalos_dir: Path):
    """Patch _resolve_dir to return our test directory."""
    return patch("legalos.profile.store._resolve_dir", return_value=legalos_dir)


def _populate(legalos_dir: Path) -> list[LearningEntry]:
    entries = [
        LearningEntry(
            id="abc12345",
            title="Test Learning",
            insight="Anti-dilution clause was aggressive",
            category=LearningCategory.CLAUSE_PATTERN,
            tags=["anti-dilution"],
        ),
        LearningEntry(
            id="def67890",
            title="Negotiation Win",
            insight="Got weighted average instead of full ratchet",
            category=LearningCategory.NEGOTIATION,
            tags=["anti-dilution", "negotiation"],
            founder_action="Pushed back successfully",
        ),
    ]
    for entry in entries:
        append_learning(entry, legalos_dir)
    return entries


class TestKbDefault:
    def test_empty_kb(self, runner: CliRunner, legalos_dir: Path):
        with _patch_resolve(legalos_dir):
            result = runner.invoke(cli, ["kb"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "No learnings yet" in result.output

    def test_kb_summary(self, runner: CliRunner, legalos_dir: Path):
        _populate(legalos_dir)
        with _patch_resolve(legalos_dir):
            result = runner.invoke(cli, ["kb"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Knowledge Base" in result.output
        assert "2 entries" in result.output


class TestKbShow:
    def test_show_empty(self, runner: CliRunner, legalos_dir: Path):
        with _patch_resolve(legalos_dir):
            result = runner.invoke(cli, ["kb", "show"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "No learnings yet" in result.output

    def test_show_entries(self, runner: CliRunner, legalos_dir: Path):
        _populate(legalos_dir)
        with _patch_resolve(legalos_dir):
            result = runner.invoke(cli, ["kb", "show"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "abc12345" in result.output
        assert "Test Learning" in result.output
        assert "def67890" in result.output


class TestKbSearch:
    def test_search_found(self, runner: CliRunner, legalos_dir: Path):
        _populate(legalos_dir)
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "search", "anti-dilution"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "2 result(s)" in result.output

    def test_search_not_found(self, runner: CliRunner, legalos_dir: Path):
        _populate(legalos_dir)
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "search", "nonexistent_xyz"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "No learnings matching" in result.output

    def test_search_with_category(self, runner: CliRunner, legalos_dir: Path):
        _populate(legalos_dir)
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "search", "anti-dilution", "--category", "negotiation"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "1 result(s)" in result.output


class TestKbRemove:
    def test_remove_existing(self, runner: CliRunner, legalos_dir: Path):
        _populate(legalos_dir)
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "remove", "abc12345"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "removed" in result.output
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 1

    def test_remove_nonexistent(self, runner: CliRunner, legalos_dir: Path):
        _populate(legalos_dir)
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "remove", "nonexistent"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "not found" in result.output


class TestKbExport:
    def test_export_to_stdout(self, runner: CliRunner, legalos_dir: Path):
        _populate(legalos_dir)
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "export"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "# Legal Knowledge Base" in result.output
        assert "Clause Patterns" in result.output

    def test_export_to_file(self, runner: CliRunner, legalos_dir: Path, tmp_path: Path):
        _populate(legalos_dir)
        output_file = tmp_path / "export.md"
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "export", "-o", str(output_file)],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "# Legal Knowledge Base" in content

    def test_export_empty(self, runner: CliRunner, legalos_dir: Path):
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "export"],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "No learnings to export" in result.output


class TestKbImport:
    def test_import_new_entries(self, runner: CliRunner, legalos_dir: Path, tmp_path: Path):
        import_data = LearningsStore(
            entries=[
                LearningEntry(title="Imported", insight="From friend"),
            ]
        )
        import_file = tmp_path / "import.json"
        import_file.write_text(import_data.model_dump_json(indent=2))

        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "import", str(import_file)],
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "1 new learning(s)" in result.output

    def test_import_nonexistent_file(self, runner: CliRunner, legalos_dir: Path):
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "import", "/nonexistent/file.json"],
                catch_exceptions=False,
            )
        assert result.exit_code != 0


class TestKbClear:
    def test_clear_confirmed(self, runner: CliRunner, legalos_dir: Path):
        _populate(legalos_dir)
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "clear"],
                input="y\n",
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "cleared" in result.output
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 0

    def test_clear_cancelled(self, runner: CliRunner, legalos_dir: Path):
        _populate(legalos_dir)
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "clear"],
                input="n\n",
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "Cancelled" in result.output
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 2

    def test_clear_empty(self, runner: CliRunner, legalos_dir: Path):
        with _patch_resolve(legalos_dir):
            result = runner.invoke(
                cli, ["kb", "clear"],
                input="y\n",
                catch_exceptions=False,
            )
        assert result.exit_code == 0
        assert "No learnings to clear" in result.output
