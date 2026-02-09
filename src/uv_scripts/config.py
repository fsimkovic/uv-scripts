"""Load and parse script definitions from pyproject.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScriptDef:
    """Normalized representation of a script definition."""

    name: str
    commands: list[str]
    env: dict[str, str] = field(default_factory=dict)
    help_text: str = ""
    is_composite: bool = False


class ConfigError(Exception):
    """Raised when pyproject.toml is missing or malformed."""


def find_pyproject(start: Path | None = None) -> Path:
    """Walk up from start (default: cwd) to find pyproject.toml."""
    current = start or Path.cwd()
    for directory in [current, *current.parents]:
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            return candidate
    raise ConfigError("No pyproject.toml found in current directory or any parent")


def load_scripts(pyproject_path: Path | None = None) -> dict[str, ScriptDef]:
    """Load and normalize all script definitions.

    Returns dict mapping script name -> ScriptDef.
    """
    path = pyproject_path or find_pyproject()

    with open(path, "rb") as f:
        data = tomllib.load(f)

    scripts_table = data.get("tool", {}).get("uvs", {}).get("scripts", {})
    if not scripts_table:
        raise ConfigError(f"No [tool.uvs.scripts] section found in {path}")

    result: dict[str, ScriptDef] = {}
    for name, value in scripts_table.items():
        result[name] = _parse_script(name, value)
    return result


def _parse_script(name: str, value: str | list | dict) -> ScriptDef:
    """Parse a single script value into a ScriptDef."""
    if isinstance(value, str):
        return ScriptDef(name=name, commands=[value])

    if isinstance(value, list):
        if not all(isinstance(v, str) for v in value):
            raise ConfigError(f"Script '{name}': array items must all be strings")
        return ScriptDef(name=name, commands=value, is_composite=True)

    if isinstance(value, dict):
        cmd = value.get("cmd")
        if not cmd or not isinstance(cmd, str):
            raise ConfigError(f"Script '{name}': table form requires a 'cmd' string")
        env = value.get("env", {})
        if not isinstance(env, dict):
            raise ConfigError(f"Script '{name}': 'env' must be a table of strings")
        help_text = value.get("help", "")
        return ScriptDef(
            name=name,
            commands=[cmd],
            env={str(k): str(v) for k, v in env.items()},
            help_text=help_text,
        )

    raise ConfigError(f"Script '{name}': value must be a string, array, or table")
