# Release Draft v0.1.0

## Summary

First public release of `minecraft-smoke-test-kit`.

This release provides a reusable smoke-test workflow for Minecraft mod projects, allowing agent-driven development flows to run `runServer` / `runClient`, detect explicit startup success markers, and stop the process automatically after successful startup.

## Highlights

- Explicit marker contract:
  - `[MC_SMOKE_OK] side=server`
  - `[MC_SMOKE_OK] side=client`
- Auto-stop orchestration script for Gradle startup validation
- Claude Code / Trellis command template
- Cursor command template
- Forge helper Java templates
- Chinese default README plus English alternative README

## Included

- `scripts/mc_smoke_test.py`
- `commands/claude/trellis/smoke-test.md`
- `commands/cursor/trellis-smoke-test.md`
- `loaders/forge/.../*.java.template`
- integration and adaptation docs
- example project layout

## Scope

Current release focuses on:

- Forge first
- explicit marker based smoke tests
- reusable agent workflow integration

## Next candidates

- NeoForge helper templates
- Fabric helper templates
- more loader-specific troubleshooting guides
- example installation scripts
