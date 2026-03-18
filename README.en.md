# Minecraft Smoke Test Kit

This project was written by BotVodka using Claude Code and GPT-5.4.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![README: 中文](https://img.shields.io/badge/README-%E4%B8%AD%E6%96%87-blue.svg)](./README.md)
[![README: English](https://img.shields.io/badge/README-English-blue.svg)](./README.en.md)

A reusable smoke-test toolkit for Minecraft mod development.

It allows an AI agent to run `runServer` / `runClient`, wait for an explicit startup success marker, and stop the process automatically after successful startup — without requiring a human to close the client window or type `stop` into the server console.

> 中文说明请见 [`README.md`](./README.md)

## What problem this solves

During Minecraft mod development, `./gradlew runServer` and `./gradlew runClient` are useful for startup verification, but they are inconvenient in agent-driven workflows:

- the process keeps running after startup
- success is often inferred from fragile logs
- shutdown usually requires manual interaction
- different projects and loaders expose different startup signals

This toolkit standardizes the workflow with a simple contract:

1. A tiny loader-specific helper logs an explicit success marker.
2. A generic Python orchestration script watches for that marker.
3. Once the marker is detected, the orchestration script stops the process in a controlled way.

## How it works

### Stable layer

These files are expected to be directly reusable across projects:

- `scripts/mc_smoke_test.py`
- `scripts/install_forge_smoke_test.py`
- a global Claude command under `~/.claude/commands/`
- `commands/cursor/trellis-smoke-test.md`

### Adaptation layer

These files depend on the target project structure and should remain templated:

- `loaders/forge/.../SmokeTestMarkers.java.template`
- `loaders/forge/.../ServerSmokeTestHooks.java.template`
- `loaders/forge/.../client/ClientSmokeTestHooks.java.template`

## Quick start

### Mode 1: Global Claude mode (recommended)

This is the recommended cross-project setup for the MVP:

- a global command is the only user entrypoint
- this repository's `scripts/mc_smoke_test.py` is the single orchestration source of truth
- target projects only keep the helper Java files that must participate in compilation

#### 1. Configure the shared kit root

Add this to your global Claude settings:

```json
{
  "env": {
    "MC_SMOKE_TEST_KIT_ROOT": "D:/projects/code/minecraft-smoke-test-kit"
  }
}
```

#### 2. Install helpers for verified environments

The only verified environment right now is Forge 1.20.1. Use helpers-only / global-mode:

```bash
python3 ./scripts/install_forge_smoke_test.py \
  --target-project "/absolute/path/to/your-project" \
  --base-package "com.example.mymod" \
  --mod-class "MyMod" \
  --global-mode
```

This path installs only:

- Forge smoke-test helper Java files

It does not copy:

- `./.trellis/scripts/mc_smoke_test.py`
- `.claude/commands/...`
- `.cursor/commands/...`

#### 3. Run smoke tests through the central script

Server:

```bash
python3 "D:/projects/code/minecraft-smoke-test-kit/scripts/mc_smoke_test.py" \
  --project-root "/absolute/path/to/your-project" \
  --task runServer \
  --side server \
  --bootstrap-helper
```

Client:

```bash
python3 "D:/projects/code/minecraft-smoke-test-kit/scripts/mc_smoke_test.py" \
  --project-root "/absolute/path/to/your-project" \
  --task runClient \
  --side client \
  --bootstrap-helper
```

#### 4. Use helper generation for unknown environments

If the target project is not the verified Forge 1.20.1 path, do not apply the existing Forge template blindly.

Use the preset helper-generation path instead:

- `docs/helper-generation-prompt.md`

### Mode 2: Project-local copy mode (legacy compatibility)

If you do not use a global Claude command, the older project-local copy mode is still available.

#### 1. Use the full installer script

```bash
python3 ./scripts/install_forge_smoke_test.py \
  --target-project "/absolute/path/to/your-project" \
  --base-package "com.example.mymod" \
  --mod-class "MyMod"
```

This script installs:

- `./.trellis/scripts/mc_smoke_test.py`
- `.claude/commands/trellis/smoke-test.md`
- `.cursor/commands/trellis-smoke-test.md`
- Forge smoke-test helper Java files

#### 2. Manually copy the orchestration script

Copy:

```text
scripts/mc_smoke_test.py
```

into your target project, for example:

```text
./.trellis/scripts/mc_smoke_test.py
```

#### 3. Manually copy the command templates

- Claude Code / Trellis:
  - `commands/claude/trellis/smoke-test.md`
- Cursor:
  - `commands/cursor/trellis-smoke-test.md`

#### 4. Manually install the Forge helper templates

Copy the Forge helper templates into your target project and replace:

- `__BASE_PACKAGE__`
- `__BASE_PACKAGE_PATH__`
- `__MOD_CLASS__`

Recommended target layout:

```text
src/main/java/<base-package>/smoketest/
src/main/java/<base-package>/smoketest/client/
```

#### 5. Run smoke tests

Server:

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runServer --side server
```

Client:

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runClient --side client
```

## Marker protocol

This project uses a single explicit marker contract:

- server: `[MC_SMOKE_OK] side=server`
- client: `[MC_SMOKE_OK] side=client`

Rules:

- helper code only logs the marker
- helper code must not terminate Minecraft on its own
- the orchestration layer owns process shutdown

## Repository layout

```text
minecraft-smoke-test-kit/
├─ README.md
├─ README.en.md
├─ LICENSE
├─ .gitignore
├─ docs/
│  ├─ integration-guide.md
│  ├─ forge-setup.md
│  ├─ adaptation-guide.md
│  ├─ command-examples.md
│  └─ github-repo-blueprint.md
├─ scripts/
│  └─ mc_smoke_test.py
├─ commands/
│  ├─ claude/trellis/
│  │  └─ smoke-test.md
│  └─ cursor/
│     └─ trellis-smoke-test.md
├─ loaders/
│  └─ forge/
│     └─ src/main/java/__BASE_PACKAGE_PATH__/
│        └─ smoketest/
│           ├─ SmokeTestMarkers.java.template
│           ├─ ServerSmokeTestHooks.java.template
│           └─ client/
│              └─ ClientSmokeTestHooks.java.template
└─ examples/
   └─ forge-example-layout.md
```

## Forge integration

See:

- `docs/integration-guide.md`
- `docs/forge-setup.md`

## Claude / Cursor command integration

This project includes parallel command templates for:

- Claude Code / Trellis
- Cursor

See:

- `docs/command-examples.md`

## Adapting to other loaders

Recommended approach:

- keep the Python orchestration script unchanged
- keep the marker protocol unchanged
- keep command parameter naming unchanged
- only replace the loader-specific helper implementation

However, the global Claude MVP should not hardcode compatibility for every loader in the global layer.

The current strategy has two layers:

1. verified layer: only Forge 1.20.1 is guaranteed to work with the existing helper templates
2. extension layer: other Minecraft versions or other loaders should use prompt-guided helper generation

That means future support for NeoForge / Fabric should primarily add generation rules and templates rather than pushing more loader-specific branching into the orchestration layer.

## Common failure modes and troubleshooting

Common failure classes:

- Gradle build failures
- directory lock / world lock conflicts
- missing explicit marker
- loader startup crashes
- Windows process-tree shutdown differences

The script prints a summary including:

- task
- side
- marker
- stop strategy
- exit result
- last log lines

## Design principles

- **KISS**: helpers only log markers
- **DRY**: process control lives in one Python script
- **YAGNI**: focus on `runServer` / `runClient` first
- **SOLID**: orchestration and loader hooks are decoupled

## License

MIT is the recommended default.

If you publish this as a standalone GitHub repository, keep the root `LICENSE` file.
