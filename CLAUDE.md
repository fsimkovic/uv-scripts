# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`uv-script` (`uvs` command) is a zero-dependency script runner for the `uv` package manager. It reads scripts defined in `[tool.uvs.scripts]` in `pyproject.toml` and executes them via `uv run`. Supports three script formats: simple strings, composite arrays (referencing other scripts), and tables with env/options.

## Common Commands

```bash
uv sync                # Install dependencies
uvs test               # Run tests (pytest tests/ -v)
uvs lint               # Lint (ruff check src/)
uvs typecheck          # Type check (ty check src/)
uvs check              # Run lint + typecheck + test
uvs format             # Auto-format (ruff format src/)
```

Run a single test file: `uv run pytest tests/test_runner.py -v`
Run a single test: `uv run pytest tests/test_runner.py::test_function_name -v`

## Architecture

Three modules in `src/uv_script/`, each with a single responsibility:

- **cli.py** — Entry point (`main()`). Parses args with argparse, loads config, delegates to runner or prints script list.
- **config.py** — Finds `pyproject.toml` by walking up the directory tree, parses `[tool.uvs.scripts]` and `[tool.uvs.editable]` sections. Normalizes all three script formats into `ScriptDef` dataclasses.
- **runner.py** — `run_script()` resolves composite scripts (detecting circular refs), wraps each command in `uv run` with editable flags and env vars, runs via subprocess.

## Code Style

- Ruff with line length 99, targeting Python 3.12+
- Enabled rules: E, F, I, UP, B, SIM
- Zero runtime dependencies — stdlib only (`tomllib`, `argparse`, `subprocess`)
- No redundant comments — don't add comments that restate what the code already expresses
- Use conventional commits exclusively (e.g. `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`)

## Testing

Tests use pytest with `unittest.mock` for subprocess and filesystem mocking. Test files mirror source modules: `test_cli.py`, `test_config.py`, `test_runner.py`.

## CI

GitHub Actions matrix tests Python 3.12, 3.13, 3.14. Publishing to PyPI happens on GitHub release via `uv build` + `pypa/gh-action-pypi-publish`.
