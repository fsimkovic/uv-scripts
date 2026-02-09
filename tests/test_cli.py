"""Tests for uv_scripts.cli."""

from unittest.mock import patch

import pytest

from uv_scripts.cli import main


@pytest.fixture
def in_project(tmp_path, monkeypatch):
    """Create a temp pyproject.toml and cd into it."""
    toml = tmp_path / "pyproject.toml"
    toml.write_text(
        '[tool.uvs.scripts]\n'
        'test = "pytest tests/"\n'
        'check = ["lint", "test"]\n'
        'lint = "ruff check ."\n'
        '\n'
        '[tool.uvs.scripts.serve]\n'
        'cmd = "flask run"\n'
        'help = "Run dev server"\n'
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestList:
    def test_list_shows_scripts(self, in_project, capsys):
        main(["--list"])
        out = capsys.readouterr().out
        assert "test" in out
        assert "serve" in out

    def test_list_output(self, in_project, capsys):
        try:
            main(["--list"])
        except SystemExit:
            pass
        out = capsys.readouterr().out
        assert "test" in out
        assert "lint" in out
        assert "check" in out
        assert "serve" in out
        assert "Run dev server" in out


class TestUnknownScript:
    def test_unknown_script_exits(self, in_project, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["nonexistent"])
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "unknown script" in err

    def test_unknown_script_suggests(self, in_project, capsys):
        with pytest.raises(SystemExit):
            main(["nonexistent"])
        err = capsys.readouterr().err
        assert "Available scripts:" in err


class TestVersion:
    def test_version_flag(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "uvs" in out


class TestNoScript:
    def test_no_args_shows_help(self, in_project, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 1


class TestRunIntegration:
    @patch("uv_scripts.runner.subprocess.run")
    def test_run_script(self, mock_run, in_project):
        mock_run.return_value.returncode = 0
        with pytest.raises(SystemExit) as exc_info:
            main(["test"])
        assert exc_info.value.code == 0
        call_args = mock_run.call_args[0][0]
        assert call_args == ["uv", "run", "pytest", "tests/"]

    @patch("uv_scripts.runner.subprocess.run")
    def test_extra_args_with_separator(self, mock_run, in_project):
        mock_run.return_value.returncode = 0
        with pytest.raises(SystemExit) as exc_info:
            main(["test", "--", "-k", "foo"])
        assert exc_info.value.code == 0
        call_args = mock_run.call_args[0][0]
        assert call_args == ["uv", "run", "pytest", "tests/", "-k", "foo"]
