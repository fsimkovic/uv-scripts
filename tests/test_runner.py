"""Tests for uv_scripts.runner."""

from unittest.mock import patch

import pytest

from uv_scripts.config import ConfigError, ScriptDef
from uv_scripts.runner import resolve_steps, run_script


@pytest.fixture
def simple_scripts():
    return {
        "lint": ScriptDef(name="lint", commands=["ruff check ."]),
        "test": ScriptDef(name="test", commands=["pytest tests/"]),
        "check": ScriptDef(name="check", commands=["lint", "test"], is_composite=True),
    }


class TestResolveSteps:
    def test_simple_script(self, simple_scripts):
        result = resolve_steps(simple_scripts["test"], simple_scripts)
        assert result == [("pytest tests/", {})]

    def test_composite_script(self, simple_scripts):
        result = resolve_steps(simple_scripts["check"], simple_scripts)
        assert [cmd for cmd, _ in result] == ["ruff check .", "pytest tests/"]

    def test_raw_command_in_composite(self):
        scripts = {
            "all": ScriptDef(name="all", commands=["echo hello", "lint"], is_composite=True),
            "lint": ScriptDef(name="lint", commands=["ruff check ."]),
        }
        result = resolve_steps(scripts["all"], scripts)
        assert [cmd for cmd, _ in result] == ["echo hello", "ruff check ."]

    def test_circular_reference_raises(self):
        scripts = {
            "a": ScriptDef(name="a", commands=["b"], is_composite=True),
            "b": ScriptDef(name="b", commands=["a"], is_composite=True),
        }
        with pytest.raises(ConfigError, match="Circular reference"):
            resolve_steps(scripts["a"], scripts)

    def test_nested_composite(self):
        scripts = {
            "lint": ScriptDef(name="lint", commands=["ruff check ."]),
            "test": ScriptDef(name="test", commands=["pytest"]),
            "check": ScriptDef(name="check", commands=["lint", "test"], is_composite=True),
            "all": ScriptDef(name="all", commands=["check"], is_composite=True),
        }
        result = resolve_steps(scripts["all"], scripts)
        assert [cmd for cmd, _ in result] == ["ruff check .", "pytest"]

    def test_env_propagated_from_referenced_script(self):
        scripts = {
            "serve": ScriptDef(
                name="serve", commands=["flask run"], env={"FLASK_DEBUG": "1"}
            ),
            "all": ScriptDef(name="all", commands=["serve"], is_composite=True),
        }
        result = resolve_steps(scripts["all"], scripts)
        assert result == [("flask run", {"FLASK_DEBUG": "1"})]

    def test_raw_command_gets_parent_env(self):
        scripts = {
            "dev": ScriptDef(
                name="dev",
                commands=["echo starting", "serve"],
                is_composite=True,
                env={"MODE": "dev"},
            ),
            "serve": ScriptDef(name="serve", commands=["flask run"]),
        }
        result = resolve_steps(scripts["dev"], scripts)
        assert result == [("echo starting", {"MODE": "dev"}), ("flask run", {})]


class TestRunScript:
    @patch("uv_scripts.runner.subprocess.run")
    def test_delegates_to_uv_run(self, mock_run, simple_scripts):
        mock_run.return_value.returncode = 0
        exit_code = run_script(simple_scripts["test"], simple_scripts)
        assert exit_code == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args == ["uv", "run", "pytest", "tests/"]

    @patch("uv_scripts.runner.subprocess.run")
    def test_stops_on_failure(self, mock_run, simple_scripts):
        mock_run.return_value.returncode = 1
        exit_code = run_script(simple_scripts["check"], simple_scripts)
        assert exit_code == 1
        assert mock_run.call_count == 1

    @patch("uv_scripts.runner.subprocess.run")
    def test_chains_on_success(self, mock_run, simple_scripts):
        mock_run.return_value.returncode = 0
        exit_code = run_script(simple_scripts["check"], simple_scripts)
        assert exit_code == 0
        assert mock_run.call_count == 2

    @patch("uv_scripts.runner.subprocess.run")
    def test_extra_args_appended_to_last(self, mock_run, simple_scripts):
        mock_run.return_value.returncode = 0
        run_script(simple_scripts["test"], simple_scripts, extra_args=["-k", "foo"])
        call_args = mock_run.call_args[0][0]
        assert call_args == ["uv", "run", "pytest", "tests/", "-k", "foo"]

    @patch("uv_scripts.runner.subprocess.run")
    def test_env_vars_merged(self, mock_run):
        mock_run.return_value.returncode = 0
        script = ScriptDef(name="s", commands=["echo"], env={"MY_VAR": "hello"})
        run_script(script, {"s": script})
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["env"]["MY_VAR"] == "hello"

    @patch("uv_scripts.runner.subprocess.run")
    def test_no_env_passes_none(self, mock_run):
        mock_run.return_value.returncode = 0
        script = ScriptDef(name="s", commands=["echo"])
        run_script(script, {"s": script})
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["env"] is None

    @patch("uv_scripts.runner.subprocess.run")
    def test_composite_uses_referenced_env(self, mock_run):
        mock_run.return_value.returncode = 0
        scripts = {
            "serve": ScriptDef(
                name="serve",
                commands=["flask run"],
                env={"FLASK_DEBUG": "1"},
            ),
            "all": ScriptDef(name="all", commands=["serve"], is_composite=True),
        }
        run_script(scripts["all"], scripts)
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["env"]["FLASK_DEBUG"] == "1"
