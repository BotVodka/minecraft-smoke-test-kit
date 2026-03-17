# Minecraft Smoke Test Kit

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
- `commands/claude/trellis/smoke-test.md`
- `commands/cursor/trellis-smoke-test.md`

### Adaptation layer

These files depend on the target project structure and should remain templated:

- `loaders/forge/.../SmokeTestMarkers.java.template`
- `loaders/forge/.../ServerSmokeTestHooks.java.template`
- `loaders/forge/.../client/ClientSmokeTestHooks.java.template`

## Quick start

### 1. Copy the orchestration script

Copy:

```text
scripts/mc_smoke_test.py
```

into your target project, for example:

```text
./.trellis/scripts/mc_smoke_test.py
```

### 2. Copy the command templates

- Claude Code / Trellis:
  - `commands/claude/trellis/smoke-test.md`
- Cursor:
  - `commands/cursor/trellis-smoke-test.md`

### 3. Install the Forge helper templates

Copy the Forge helper templates into your target project and replace:

- `__BASE_PACKAGE__`
- `__BASE_PACKAGE_PATH__`
- `__MOD_ID__`
- `__MOD_CLASS__`

Recommended target layout:

```text
src/main/java/<base-package>/smoketest/
src/main/java/<base-package>/smoketest/client/
```

### 4. Run smoke tests

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

That means future support for NeoForge / Fabric should primarily add helper templates rather than rewrite the orchestration layer.

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
