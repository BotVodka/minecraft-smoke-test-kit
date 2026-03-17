# Auto-Stop Minecraft Smoke Test

Run a Gradle Minecraft smoke test, wait for an explicit success marker, then stop automatically without manual console interaction.

## Current Repo Usage

### Dedicated server

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runServer --side server
```

### Client

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runClient --side client
```

## What This Command Should Do

1. Confirm which Gradle task to run and which side it targets.
2. Use `python3 ./.trellis/scripts/mc_smoke_test.py` instead of leaving `./gradlew runServer` or `./gradlew runClient` hanging.
3. Wait for the explicit marker:
   - server: `[MC_SMOKE_OK] side=server`
   - client: `[MC_SMOKE_OK] side=client`
4. Stop automatically after success:
   - `server` -> terminate the process tree in a controlled way
   - `client` -> terminate the process tree in a controlled way
5. Report:
   - task name
   - marker used
   - stop strategy used
   - whether the marker was seen
   - exit result / failure reason

## Parameterized Variants

Use these flags when adapting to another loader or project:

```bash
python3 ./.trellis/scripts/mc_smoke_test.py \
  --project-root "/absolute/path/to/project" \
  --task runServer \
  --side server \
  --marker "[MC_SMOKE_OK] side=server" \
  --stop-strategy kill-tree
```

```bash
python3 ./.trellis/scripts/mc_smoke_test.py \
  --project-root "/absolute/path/to/project" \
  --task runClient \
  --side client \
  --marker "[MC_SMOKE_OK] side=client" \
  --stop-strategy kill-tree
```

Optional extension flags:
- `--gradle-arg <arg>` for environment-specific Gradle flags such as certificate or JVM settings
- `--success-regex <regex>` for loader-specific fallback success signals
- `--failure-regex <regex>` for project-specific failure hints
- `--marker-timeout-seconds <seconds>`
- `--shutdown-timeout-seconds <seconds>`

## New Environment Helper Template

If the target project does not already emit an explicit marker, first generate a minimal helper using this approach:

### Requirements for the helper

- Put it in a focused smoke-test package
- Reuse the project logger
- Print exactly one explicit success marker per side
- Do not add auto-exit logic into the helper
- Keep server and client handling separate

### Prompt template

```text
Create a minimal Minecraft smoke-test helper for this project.

Goal:
- Emit an explicit success marker for smoke-test orchestration.
- Do not exit the game/process from the helper.

Requirements:
- Add a focused smoke-test package.
- Add one server-side hook that logs: [MC_SMOKE_OK] side=server
- Add one client-side hook that logs: [MC_SMOKE_OK] side=client
- Keep the main mod entrypoint thin.
- Reuse the existing project logger style.
- Prefer the earliest stable lifecycle point that proves successful startup.
- Do not add unrelated abstractions.

Deliverables:
1. Helper classes
2. Any minimal registration/event wiring required
3. The exact marker strings used
4. Which lifecycle event each side uses and why
```

## Output Format

```markdown
## Smoke Test Result

- Task: <gradle-task>
- Side: <server|client>
- Marker: <marker>
- Stop Strategy: <strategy>
- Result: Passed | Failed

### Evidence
- <marker seen / failure signal / exit code>

### Notes
- <follow-up if the helper is missing or needs adaptation>
```
