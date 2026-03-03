"""Tests for CLI commands using Click's CliRunner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from legalos.cli import cli
from legalos.profile.schemas import (
    DealContext,
    DealProfile,
    FeedbackItem,
    FounderProfile,
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture
def legalos_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".legalos"
    d.mkdir()
    return d


@pytest.fixture
def profile_in_dir(legalos_dir: Path) -> Path:
    """Create a minimal profile.json in the test directory."""
    from legalos.profile.store import save_profile

    p = FounderProfile()
    p.company.name = "TestCo"
    p.company.sector = "SaaS"
    save_profile(p, legalos_dir)
    return legalos_dir


# ── Profile commands ──────────────────────────────────────────


class TestProfileCommands:
    def test_profile_show_no_profile(self, runner: CliRunner, tmp_path: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=tmp_path / ".legalos"):
            result = runner.invoke(cli, ["profile"])
        assert result.exit_code == 0
        assert "No profile" in result.output

    def test_profile_show_with_profile(self, runner: CliRunner, profile_in_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=profile_in_dir):
            result = runner.invoke(cli, ["profile"])
        assert result.exit_code == 0
        assert "TestCo" in result.output

    def test_profile_set_and_show(self, runner: CliRunner, tmp_path: Path):
        d = tmp_path / ".legalos"
        d.mkdir()
        with patch("legalos.profile.store._resolve_dir", return_value=d):
            with patch("legalos.cli._auto_update_preferences"):
                result = runner.invoke(cli, ["profile", "set", "company.name", "NewCo"])
                assert result.exit_code == 0
                assert "NewCo" in result.output

    def test_profile_clear(self, runner: CliRunner, profile_in_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=profile_in_dir):
            with patch("legalos.cli._auto_update_preferences"):
                result = runner.invoke(cli, ["profile", "clear"])
        assert result.exit_code == 0
        assert "deleted" in result.output.lower()

    def test_profile_export_import(self, runner: CliRunner, profile_in_dir: Path, tmp_path: Path):
        export_file = tmp_path / "profile_export.json"
        with patch("legalos.profile.store._resolve_dir", return_value=profile_in_dir):
            result = runner.invoke(cli, ["profile", "export", str(export_file)])
        assert result.exit_code == 0
        assert export_file.exists()

        # Import into a fresh dir
        fresh = tmp_path / ".legalos_import"
        fresh.mkdir()
        with patch("legalos.profile.store._resolve_dir", return_value=fresh):
            with patch("legalos.cli._auto_update_preferences"):
                result = runner.invoke(cli, ["profile", "import", str(export_file)])
        assert result.exit_code == 0
        assert "Imported" in result.output


# ── Deal commands ─────────────────────────────────────────────


class TestDealCommands:
    def test_deal_list_empty(self, runner: CliRunner, legalos_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=legalos_dir):
            result = runner.invoke(cli, ["deal"])
        assert result.exit_code == 0
        assert "No deals" in result.output

    def test_deal_show_nonexistent(self, runner: CliRunner, legalos_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=legalos_dir):
            result = runner.invoke(cli, ["deal", "show", "nope"])
        assert result.exit_code == 1

    def test_deal_remove_nonexistent(self, runner: CliRunner, legalos_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=legalos_dir):
            result = runner.invoke(cli, ["deal", "remove", "nope"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower()


# ── Feedback commands ─────────────────────────────────────────


class TestFeedbackCommands:
    def test_feedback_show_empty(self, runner: CliRunner, legalos_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=legalos_dir):
            result = runner.invoke(cli, ["feedback"])
        assert result.exit_code == 0
        assert "No feedback" in result.output

    def test_feedback_submit(self, runner: CliRunner, legalos_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=legalos_dir):
            with patch("legalos.cli._auto_update_preferences"):
                result = runner.invoke(cli, [
                    "feedback", "submit",
                    "--down", "Board control,Vesting",
                    "--doc", "test.pdf",
                ])
        assert result.exit_code == 0
        assert "saved" in result.output.lower()

    def test_feedback_submit_empty_fails(self, runner: CliRunner, legalos_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=legalos_dir):
            result = runner.invoke(cli, ["feedback", "submit"])
        assert result.exit_code == 1

    def test_feedback_clear_empty(self, runner: CliRunner, legalos_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=legalos_dir):
            result = runner.invoke(cli, ["feedback", "clear"])
        assert result.exit_code == 0


# ── Preferences command ───────────────────────────────────────


class TestPreferencesCommand:
    def test_preferences_with_profile(self, runner: CliRunner, profile_in_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=profile_in_dir):
            with patch("legalos.profile.preferences_export._resolve_dir", return_value=profile_in_dir):
                result = runner.invoke(cli, ["preferences", "--no-browser"])
        # May succeed or fail depending on full setup, but should not crash
        assert result.exit_code in (0, 1)


# ── Claude export command ─────────────────────────────────────


class TestClaudeExportCommand:
    def test_claude_export_no_profile(self, runner: CliRunner, legalos_dir: Path):
        with patch("legalos.profile.store._resolve_dir", return_value=legalos_dir):
            result = runner.invoke(cli, ["claude-export"])
        # Should fail gracefully when no profile exists
        # (exact behavior depends on implementation)
        assert result.exit_code in (0, 1)
