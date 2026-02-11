# Session Context

## User Prompts

### Prompt 1

Implement the following plan:

# Add `features` (optional dependencies) support to uvs

## Context

uvs currently has no way to install optional dependency groups (extras) when running scripts. Users who define `[project.optional-dependencies]` in their `pyproject.toml` can't opt into those extras via uvs. Adding a `features` config key (mirroring Hatch's convention) lets users declare which extras to install, translating to `--extra <name>` flags on every `uv run` invocation.

## Changes

### 1...

### Prompt 2

commit this

