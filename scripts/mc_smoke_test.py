#!/usr/bin/env python3
"""Gradle-based Minecraft smoke test orchestration with explicit success markers."""

from __future__ import annotations

import argparse
import os
import queue
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Iterable, Pattern


DEFAULT_MARKER_PREFIX = "[MC_SMOKE_OK]"
DEFAULT_MARKER_TIMEOUT_SECONDS = 600.0
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS = 60.0
DEFAULT_LAST_LINES = 60
SERVER_DONE_PATTERN = r'Done \([^\n]+\)! For help, type "help"'
BUILD_FAILED_PATTERN = r"BUILD FAILED"
SERVER_START_FAILED_PATTERN = r"Failed to start the minecraft server"
DIRECTORY_LOCK_PATTERN = r"DirectoryLock|另一个程序已锁定文件的一部分"
EXCEPTION_PATTERN = r"\bFATAL\b|Crash report|A problem occurred|Mixin apply failed"
FORGE_PLUGIN_PATTERN = r"net\.minecraftforge\.gradle"
FORGE_MODLOADER_PATTERN = r'modLoader\s*=\s*"javafml"'
CLASS_PATTERN = re.compile(r"\bclass\s+(?P<name>[A-Za-z_]\w*)\b")
PACKAGE_PATTERN = re.compile(r"^\s*package\s+(?P<name>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*;", re.MULTILINE)
PROPERTY_PATTERN = re.compile(r"^\s*(?P<key>[A-Za-z0-9_.-]+)\s*=\s*(?P<value>.*?)\s*$")
HELPER_RELATIVE_PATHS = (
    Path("src/main/java") / "**" / "smoketest" / "SmokeTestMarkers.java",
    Path("src/main/java") / "**" / "smoketest" / "ServerSmokeTestHooks.java",
    Path("src/main/java") / "**" / "smoketest" / "client" / "ClientSmokeTestHooks.java",
)


@dataclass(frozen=True)
class SmokeTestConfig:
    project_root: Path
    task: str
    side: str
    marker: str
    stop_strategy: str
    marker_timeout_seconds: float
    shutdown_timeout_seconds: float
    gradle_args: tuple[str, ...]
    success_patterns: tuple[Pattern[str], ...]
    failure_patterns: tuple[Pattern[str], ...]
    last_lines: int
    bootstrap_helper: bool

    @property
    def gradle_command(self) -> str:
        return shlex.join(["./gradlew", *self.gradle_args, self.task])


@dataclass(frozen=True)
class ProjectInspection:
    helper_present: bool
    missing_helpers: tuple[str, ...]
    loader: str | None
    minecraft_version: str | None
    verified_environment: bool
    base_package: str | None
    mod_class: str | None


@dataclass
class SmokeTestResult:
    success: bool
    reason: str
    exit_code: int | None
    marker_seen: bool
    stop_attempted: bool
    matched_success_signal: str | None
    matched_failure_signal: str | None
    duration_seconds: float
    last_lines: list[str]
    helper_status: str
    script_source: str
    loader: str | None
    minecraft_version: str | None


def compile_patterns(values: Iterable[str]) -> tuple[Pattern[str], ...]:
    return tuple(re.compile(value) for value in values)


def default_marker_for_side(side: str) -> str:
    return f"{DEFAULT_MARKER_PREFIX} side={side}"


def default_success_regexes(side: str) -> list[str]:
    regexes: list[str] = []
    if side == "server":
        regexes.append(SERVER_DONE_PATTERN)
    return regexes


def default_failure_regexes() -> list[str]:
    return [
        BUILD_FAILED_PATTERN,
        SERVER_START_FAILED_PATTERN,
        DIRECTORY_LOCK_PATTERN,
        EXCEPTION_PATTERN,
    ]


def parse_args() -> SmokeTestConfig:
    parser = argparse.ArgumentParser(
        description="Run a Gradle Minecraft smoke test, watch for an explicit marker, then stop automatically."
    )
    parser.add_argument("--project-root", default=".", help="Project root containing the Gradle wrapper.")
    parser.add_argument("--task", required=True, help="Gradle task to run, such as runServer or runClient.")
    parser.add_argument("--side", required=True, choices=("server", "client"), help="Smoke test side.")
    parser.add_argument("--marker", help="Explicit success marker to wait for.")
    parser.add_argument(
        "--stop-strategy",
        choices=("kill-tree",),
        help="How to stop after success. The current repository uses kill-tree for both server and client.",
    )
    parser.add_argument(
        "--bootstrap-helper",
        action="store_true",
        help="If helper files are missing, auto-install verified Forge 1.20.1 helper files before running.",
    )
    parser.add_argument(
        "--marker-timeout-seconds",
        type=float,
        default=DEFAULT_MARKER_TIMEOUT_SECONDS,
        help="Maximum seconds to wait for the marker before failing.",
    )
    parser.add_argument(
        "--shutdown-timeout-seconds",
        type=float,
        default=DEFAULT_SHUTDOWN_TIMEOUT_SECONDS,
        help="Maximum seconds to wait for shutdown after stop is requested.",
    )
    parser.add_argument(
        "--gradle-arg",
        action="append",
        default=[],
        help="Additional argument passed through to Gradle before the task name. Can be passed multiple times.",
    )
    parser.add_argument(
        "--success-regex",
        action="append",
        default=[],
        help="Additional success regex. Can be passed multiple times.",
    )
    parser.add_argument(
        "--failure-regex",
        action="append",
        default=[],
        help="Failure regex to highlight in logs. Can be passed multiple times.",
    )
    parser.add_argument(
        "--last-lines",
        type=int,
        default=DEFAULT_LAST_LINES,
        help="Number of trailing log lines to include in summaries.",
    )

    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    marker = args.marker or default_marker_for_side(args.side)
    stop_strategy = args.stop_strategy or "kill-tree"
    success_patterns = compile_patterns(default_success_regexes(args.side) + list(args.success_regex))
    failure_patterns = compile_patterns(default_failure_regexes() + list(args.failure_regex))

    return SmokeTestConfig(
        project_root=project_root,
        task=args.task,
        side=args.side,
        marker=marker,
        stop_strategy=stop_strategy,
        marker_timeout_seconds=args.marker_timeout_seconds,
        shutdown_timeout_seconds=args.shutdown_timeout_seconds,
        gradle_args=tuple(args.gradle_arg),
        success_patterns=success_patterns,
        failure_patterns=failure_patterns,
        last_lines=max(10, args.last_lines),
        bootstrap_helper=args.bootstrap_helper,
    )


def fail(message: str) -> None:
    print(f"[mc-smoke] {message}", file=sys.stderr, flush=True)
    raise SystemExit(2)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_gradle_properties(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = PROPERTY_PATTERN.match(raw_line)
        if match is None:
            continue
        values[match.group("key")] = match.group("value")
    return values


def is_valid_java_package(value: str | None) -> bool:
    if not value:
        return False
    parts = value.split(".")
    return all(part and part.isidentifier() for part in parts)


def detect_helper_files(project_root: Path) -> tuple[bool, tuple[str, ...]]:
    missing: list[str] = []
    for relative_pattern in HELPER_RELATIVE_PATHS:
        matches = list(project_root.glob(str(relative_pattern)))
        if not matches:
            missing.append(str(relative_pattern).replace("\\", "/"))
    return not missing, tuple(missing)


def detect_loader(project_root: Path) -> str | None:
    build_gradle = read_text_if_exists(project_root / "build.gradle")
    mods_toml = read_text_if_exists(project_root / "src/main/resources/META-INF/mods.toml")
    if re.search(FORGE_PLUGIN_PATTERN, build_gradle) or re.search(FORGE_MODLOADER_PATTERN, mods_toml):
        return "forge"
    return None


def find_mod_entrypoint(project_root: Path, package_hint: str | None) -> tuple[str | None, str | None]:
    java_root = project_root / "src/main/java"
    if not java_root.exists():
        return None, None

    search_roots: list[Path] = []
    if package_hint and is_valid_java_package(package_hint):
        hinted_root = java_root / Path(*package_hint.split("."))
        if hinted_root.exists():
            search_roots.append(hinted_root)
    search_roots.append(java_root)

    seen: set[Path] = set()
    for search_root in search_roots:
        for path in search_root.rglob("*.java"):
            if path in seen:
                continue
            seen.add(path)
            content = read_text_if_exists(path)
            if "@Mod(" not in content:
                continue
            package_match = PACKAGE_PATTERN.search(content)
            class_match = CLASS_PATTERN.search(content)
            if package_match and class_match:
                return package_match.group("name"), class_match.group("name")
    return None, None


def inspect_project(project_root: Path) -> ProjectInspection:
    properties = parse_gradle_properties(project_root / "gradle.properties")
    helper_present, missing_helpers = detect_helper_files(project_root)
    loader = detect_loader(project_root)
    minecraft_version = properties.get("minecraft_version")
    verified_environment = loader == "forge" and minecraft_version == "1.20.1"

    base_package = properties.get("mod_group_id")
    if not is_valid_java_package(base_package):
        base_package = None

    entry_package, mod_class = find_mod_entrypoint(project_root, base_package)
    if base_package is None:
        base_package = entry_package

    return ProjectInspection(
        helper_present=helper_present,
        missing_helpers=missing_helpers,
        loader=loader,
        minecraft_version=minecraft_version,
        verified_environment=verified_environment,
        base_package=base_package,
        mod_class=mod_class,
    )


def run_helper_bootstrap(project_root: Path, inspection: ProjectInspection) -> ProjectInspection:
    if inspection.base_package is None or inspection.mod_class is None:
        fail(
            "smoke-test helper is missing and automatic bootstrap could not detect base package or mod class; "
            "verify gradle.properties mod_group_id and the @Mod entrypoint class first"
        )

    installer_path = repo_root() / "scripts" / "install_forge_smoke_test.py"
    if not installer_path.exists():
        fail(f"Forge helper installer not found: {installer_path}")

    command = [
        sys.executable,
        str(installer_path),
        "--target-project",
        str(project_root),
        "--base-package",
        inspection.base_package,
        "--mod-class",
        inspection.mod_class,
        "--global-mode",
    ]
    print("[mc-smoke] smoke-test helper missing; bootstrapping verified Forge helper files", flush=True)
    print(f"[mc-smoke] bootstrap command: {shlex.join(command)}", flush=True)
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        fail(f"helper bootstrap failed with exit code {completed.returncode}")

    refreshed = inspect_project(project_root)
    if not refreshed.helper_present:
        missing = ", ".join(refreshed.missing_helpers)
        fail(f"helper bootstrap completed but helper files are still missing: {missing}")
    return refreshed


def validate_config(config: SmokeTestConfig) -> tuple[ProjectInspection, str]:
    if not config.project_root.exists():
        fail(f"project root does not exist: {config.project_root}")

    gradlew_path = config.project_root / "gradlew"
    if not gradlew_path.exists():
        fail(f"Gradle wrapper not found: {gradlew_path}")

    if shutil.which("bash") is None:
        fail("bash executable not found on PATH; the smoke-test runner requires bash-compatible Gradle invocation")

    if os.name == "nt" and config.stop_strategy == "kill-tree" and shutil.which("taskkill") is None:
        fail("taskkill executable not found on PATH; Windows kill-tree shutdown requires taskkill")

    inspection = inspect_project(config.project_root)
    helper_status = "existing"
    if not inspection.helper_present:
        missing = ", ".join(inspection.missing_helpers)
        if not config.bootstrap_helper:
            fail(
                "smoke-test helper is missing: "
                f"{missing}. Re-run with --bootstrap-helper or install helper files first."
            )
        if not inspection.verified_environment:
            fail(
                "project is not in the verified Forge 1.20.1 MVP support range; "
                "do not auto-apply the Forge template. Use docs/helper-generation-prompt.md instead."
            )
        inspection = run_helper_bootstrap(config.project_root, inspection)
        helper_status = "installed"

    return inspection, helper_status


def create_process(config: SmokeTestConfig) -> subprocess.Popen[str]:
    bash_executable = shutil.which("bash")
    if bash_executable is None:
        fail("bash executable not found on PATH")

    command = [bash_executable, "-lc", config.gradle_command]
    print(f"[mc-smoke] starting command: {config.gradle_command}", flush=True)
    return subprocess.Popen(
        command,
        cwd=config.project_root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        start_new_session=(os.name != "nt"),
    )


def spawn_output_reader(process: subprocess.Popen[str], output_queue: queue.Queue[str | None]) -> threading.Thread:
    if process.stdout is None:
        fail("process stdout pipe was not created")

    def reader() -> None:
        try:
            for line in process.stdout:
                output_queue.put(line)
        finally:
            output_queue.put(None)

    thread = threading.Thread(target=reader, name="mc-smoke-output-reader", daemon=True)
    thread.start()
    return thread


def print_summary(config: SmokeTestConfig, result: SmokeTestResult) -> None:
    print("[mc-smoke] --- summary ---", flush=True)
    print(f"[mc-smoke] project_root={config.project_root}", flush=True)
    print(f"[mc-smoke] script_source={result.script_source}", flush=True)
    print(f"[mc-smoke] helper_status={result.helper_status}", flush=True)
    if result.loader is not None:
        print(f"[mc-smoke] loader={result.loader}", flush=True)
    if result.minecraft_version is not None:
        print(f"[mc-smoke] minecraft_version={result.minecraft_version}", flush=True)
    print(f"[mc-smoke] task={config.task}", flush=True)
    print(f"[mc-smoke] side={config.side}", flush=True)
    print(f"[mc-smoke] marker={config.marker}", flush=True)
    print(f"[mc-smoke] stop_strategy={config.stop_strategy}", flush=True)
    if config.gradle_args:
        print(f"[mc-smoke] gradle_args={list(config.gradle_args)}", flush=True)
    print(f"[mc-smoke] marker_seen={result.marker_seen}", flush=True)
    print(f"[mc-smoke] stop_attempted={result.stop_attempted}", flush=True)
    print(f"[mc-smoke] success={result.success}", flush=True)
    print(f"[mc-smoke] reason={result.reason}", flush=True)
    print(f"[mc-smoke] exit_code={result.exit_code}", flush=True)
    print(f"[mc-smoke] duration_seconds={result.duration_seconds:.1f}", flush=True)
    if result.matched_success_signal:
        print(f"[mc-smoke] matched_success_signal={result.matched_success_signal}", flush=True)
    if result.matched_failure_signal:
        print(f"[mc-smoke] matched_failure_signal={result.matched_failure_signal}", flush=True)
    if result.last_lines:
        print("[mc-smoke] last_log_lines:", flush=True)
        for line in result.last_lines:
            print(f"[mc-smoke]   {safe_console_text(line)}", flush=True)


def safe_console_text(value: str) -> str:
    return value.encode("ascii", errors="backslashreplace").decode("ascii")


def kill_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    print(f"[mc-smoke] terminating process tree for pid {process.pid}", flush=True)
    if os.name == "nt":
        completed = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.stdout.strip():
            print(f"[mc-smoke] taskkill stdout: {safe_console_text(completed.stdout.strip())}", flush=True)
        if completed.stderr.strip():
            print(f"[mc-smoke] taskkill stderr: {safe_console_text(completed.stderr.strip())}", flush=True)
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except ProcessLookupError:
            return


def request_stop(process: subprocess.Popen[str], config: SmokeTestConfig) -> bool:
    kill_process_tree(process)
    return True


def wait_for_process_exit(process: subprocess.Popen[str], timeout_seconds: float) -> int | None:
    try:
        return process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        return process.poll()


def drain_output(
    output_queue: queue.Queue[str | None],
    lines: Deque[str],
    marker: str,
    success_patterns: tuple[Pattern[str], ...],
    failure_patterns: tuple[Pattern[str], ...],
) -> tuple[bool, str | None, str | None, bool]:
    marker_seen = False
    matched_success_signal: str | None = None
    matched_failure_signal: str | None = None
    stream_closed = False

    while True:
        try:
            item = output_queue.get_nowait()
        except queue.Empty:
            break

        if item is None:
            stream_closed = True
            break

        line = item.rstrip("\r\n")
        lines.append(line)
        print(safe_console_text(line), flush=True)

        if marker in line and not marker_seen:
            marker_seen = True
            matched_success_signal = marker
            print(f"[mc-smoke] explicit marker detected: {marker}", flush=True)

        if matched_success_signal is None:
            for pattern in success_patterns:
                if pattern.search(line):
                    matched_success_signal = pattern.pattern
                    print(f"[mc-smoke] success regex matched: {pattern.pattern}", flush=True)
                    break

        if matched_failure_signal is None:
            for pattern in failure_patterns:
                if pattern.search(line):
                    matched_failure_signal = pattern.pattern
                    print(f"[mc-smoke] failure regex matched: {pattern.pattern}", flush=True)
                    break

    return marker_seen, matched_success_signal, matched_failure_signal, stream_closed


def run_smoke_test(config: SmokeTestConfig, inspection: ProjectInspection, helper_status: str) -> SmokeTestResult:
    process = create_process(config)
    output_queue: queue.Queue[str | None] = queue.Queue()
    output_reader = spawn_output_reader(process, output_queue)
    last_lines: Deque[str] = deque(maxlen=config.last_lines)

    start_time = time.monotonic()
    deadline = start_time + config.marker_timeout_seconds
    marker_seen = False
    stop_attempted = False
    matched_success_signal: str | None = None
    matched_failure_signal: str | None = None

    try:
        while True:
            batch_marker_seen, batch_success_signal, batch_failure_signal, stream_closed = drain_output(
                output_queue,
                last_lines,
                config.marker,
                config.success_patterns,
                config.failure_patterns,
            )
            marker_seen = marker_seen or batch_marker_seen
            matched_success_signal = matched_success_signal or batch_success_signal
            matched_failure_signal = matched_failure_signal or batch_failure_signal

            if matched_success_signal is not None:
                stop_attempted = request_stop(process, config)
                shutdown_deadline = time.monotonic() + config.shutdown_timeout_seconds
                while time.monotonic() < shutdown_deadline:
                    drain_marker_seen, drain_success_signal, drain_failure_signal, _ = drain_output(
                        output_queue,
                        last_lines,
                        config.marker,
                        config.success_patterns,
                        config.failure_patterns,
                    )
                    marker_seen = marker_seen or drain_marker_seen
                    matched_success_signal = matched_success_signal or drain_success_signal
                    matched_failure_signal = matched_failure_signal or drain_failure_signal

                    if process.poll() is not None:
                        exit_code = process.returncode
                        duration_seconds = time.monotonic() - start_time
                        success = config.stop_strategy == "kill-tree" or exit_code == 0
                        reason = "marker detected and process stopped" if success else "marker detected but shutdown returned non-zero"
                        return SmokeTestResult(
                            success=success,
                            reason=reason,
                            exit_code=exit_code,
                            marker_seen=marker_seen,
                            stop_attempted=stop_attempted,
                            matched_success_signal=matched_success_signal,
                            matched_failure_signal=matched_failure_signal,
                            duration_seconds=duration_seconds,
                            last_lines=list(last_lines),
                            helper_status=helper_status,
                            script_source="central",
                            loader=inspection.loader,
                            minecraft_version=inspection.minecraft_version,
                        )

                    time.sleep(0.2)

                kill_process_tree(process)
                exit_code = wait_for_process_exit(process, timeout_seconds=10)
                return SmokeTestResult(
                    success=False,
                    reason="marker detected but shutdown timed out",
                    exit_code=exit_code,
                    marker_seen=marker_seen,
                    stop_attempted=stop_attempted,
                    matched_success_signal=matched_success_signal,
                    matched_failure_signal=matched_failure_signal,
                    duration_seconds=time.monotonic() - start_time,
                    last_lines=list(last_lines),
                    helper_status=helper_status,
                    script_source="central",
                    loader=inspection.loader,
                    minecraft_version=inspection.minecraft_version,
                )

            if process.poll() is not None:
                reason = "process exited before explicit marker was detected"
                if matched_failure_signal is not None:
                    reason = f"process exited before explicit marker was detected; matched failure signal: {matched_failure_signal}"
                return SmokeTestResult(
                    success=False,
                    reason=reason,
                    exit_code=process.returncode,
                    marker_seen=marker_seen,
                    stop_attempted=stop_attempted,
                    matched_success_signal=matched_success_signal,
                    matched_failure_signal=matched_failure_signal,
                    duration_seconds=time.monotonic() - start_time,
                    last_lines=list(last_lines),
                    helper_status=helper_status,
                    script_source="central",
                    loader=inspection.loader,
                    minecraft_version=inspection.minecraft_version,
                )

            if time.monotonic() >= deadline:
                kill_process_tree(process)
                exit_code = wait_for_process_exit(process, timeout_seconds=10)
                return SmokeTestResult(
                    success=False,
                    reason="timed out waiting for explicit marker",
                    exit_code=exit_code,
                    marker_seen=marker_seen,
                    stop_attempted=stop_attempted,
                    matched_success_signal=matched_success_signal,
                    matched_failure_signal=matched_failure_signal,
                    duration_seconds=time.monotonic() - start_time,
                    last_lines=list(last_lines),
                    helper_status=helper_status,
                    script_source="central",
                    loader=inspection.loader,
                    minecraft_version=inspection.minecraft_version,
                )

            if stream_closed and not marker_seen:
                return SmokeTestResult(
                    success=False,
                    reason="output stream closed before explicit marker was detected",
                    exit_code=process.poll(),
                    marker_seen=marker_seen,
                    stop_attempted=stop_attempted,
                    matched_success_signal=matched_success_signal,
                    matched_failure_signal=matched_failure_signal,
                    duration_seconds=time.monotonic() - start_time,
                    last_lines=list(last_lines),
                    helper_status=helper_status,
                    script_source="central",
                    loader=inspection.loader,
                    minecraft_version=inspection.minecraft_version,
                )

            time.sleep(0.2)
    finally:
        output_reader.join(timeout=2)
        if process.poll() is None:
            kill_process_tree(process)
            wait_for_process_exit(process, timeout_seconds=10)


def main() -> int:
    config = parse_args()
    inspection, helper_status = validate_config(config)
    result = run_smoke_test(config, inspection, helper_status)
    print_summary(config, result)
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
