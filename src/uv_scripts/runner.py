"""Execute scripts by delegating to uv run."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys

from .config import ScriptDef


def run_script(
    script: ScriptDef,
    all_scripts: dict[str, ScriptDef],
    extra_args: list[str] | None = None,
    verbose: bool = False,
) -> int:
    """Execute a script definition. Returns exit code (0 = success)."""
    commands = resolve_commands(script, all_scripts)

    for i, cmd_str in enumerate(commands):
        if extra_args and i == len(commands) - 1:
            cmd_str = cmd_str + " " + " ".join(shlex.quote(a) for a in extra_args)

        exit_code = _exec_one(cmd_str, script.env, verbose)
        if exit_code != 0:
            return exit_code

    return 0


def resolve_commands(
    script: ScriptDef,
    all_scripts: dict[str, ScriptDef],
    _seen: set[str] | None = None,
) -> list[str]:
    """Resolve composite scripts into a flat command list.

    Handles references to other scripts and detects cycles.
    """
    if _seen is None:
        _seen = set()

    if script.name in _seen:
        print(f"uvs: circular reference detected: {script.name}", file=sys.stderr)
        sys.exit(1)
    _seen.add(script.name)

    if not script.is_composite:
        return list(script.commands)

    result: list[str] = []
    for item in script.commands:
        if item in all_scripts:
            referenced = all_scripts[item]
            result.extend(resolve_commands(referenced, all_scripts, _seen.copy()))
        else:
            result.append(item)

    return result


def _exec_one(cmd_str: str, env: dict[str, str], verbose: bool) -> int:
    """Execute a single command string via uv run."""
    parts = shlex.split(cmd_str)
    full_cmd = ["uv", "run"] + parts

    if verbose:
        env_prefix = " ".join(f"{k}={v}" for k, v in env.items())
        display = f"{env_prefix} {' '.join(full_cmd)}".strip()
        print(f"$ {display}", file=sys.stderr)

    run_env = None
    if env:
        run_env = {**os.environ, **env}

    result = subprocess.run(full_cmd, env=run_env)
    return result.returncode
