from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


INSTALL_MODE_FULL = "full"
INSTALL_MODE_HELPERS_ONLY = "helpers-only"


@dataclass(frozen=True)
class InstallConfig:
    target_project: Path
    base_package: str
    mod_class: str
    force: bool
    install_mode: str

    @property
    def helpers_only(self) -> bool:
        return self.install_mode == INSTALL_MODE_HELPERS_ONLY


@dataclass(frozen=True)
class InstallPlan:
    direct_copies: tuple[tuple[Path, Path], ...]
    template_targets: tuple[tuple[Path, Path], ...]


def parse_args() -> InstallConfig:
    parser = argparse.ArgumentParser(
        description="Install the Forge smoke-test kit into a target project.",
    )
    parser.add_argument(
        "--target-project",
        required=True,
        help="Absolute or relative path to the target project root.",
    )
    parser.add_argument(
        "--base-package",
        required=True,
        help='Java base package, for example "com.example.mymod".',
    )
    parser.add_argument(
        "--mod-class",
        required=True,
        help='Main mod class name, for example "MyMod".',
    )
    parser.add_argument(
        "--install-mode",
        choices=(INSTALL_MODE_FULL, INSTALL_MODE_HELPERS_ONLY),
        default=INSTALL_MODE_FULL,
        help="Installation scope: full installs script + command templates + helpers, helpers-only installs only the Forge helper Java files.",
    )
    parser.add_argument(
        "--global-mode",
        action="store_true",
        help="Shortcut for Claude global mode. Equivalent to --install-mode helpers-only and prints central-script next steps.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing target files.",
    )
    args = parser.parse_args()

    install_mode = INSTALL_MODE_HELPERS_ONLY if args.global_mode else args.install_mode
    target_project = Path(args.target_project).resolve()
    if not target_project.exists():
        raise SystemExit(f"Target project does not exist: {target_project}")

    return InstallConfig(
        target_project=target_project,
        base_package=args.base_package,
        mod_class=args.mod_class,
        force=args.force,
        install_mode=install_mode,
    )


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def validate_base_package(base_package: str) -> list[str]:
    parts = base_package.split(".")
    if not parts or any(not part or not part.isidentifier() for part in parts):
        raise SystemExit(f"Invalid base package: {base_package}")
    return parts


def validate_mod_class(mod_class: str) -> None:
    if not mod_class.isidentifier():
        raise SystemExit(f"Invalid mod class: {mod_class}")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def copy_file(source: Path, target: Path, force: bool) -> None:
    if target.exists() and not force:
        raise SystemExit(f"Target already exists: {target}. Use --force to overwrite.")
    ensure_parent(target)
    shutil.copy2(source, target)


def render_template(source: Path, target: Path, replacements: dict[str, str], force: bool) -> None:
    if target.exists() and not force:
        raise SystemExit(f"Target already exists: {target}. Use --force to overwrite.")
    content = source.read_text(encoding="utf-8")
    for old, new in replacements.items():
        content = content.replace(old, new)
    ensure_parent(target)
    target.write_text(content, encoding="utf-8", newline="\n")


def build_install_plan(config: InstallConfig) -> InstallPlan:
    root = repo_root()
    base_package_parts = validate_base_package(config.base_package)
    validate_mod_class(config.mod_class)

    direct_copies: list[tuple[Path, Path]] = []
    if not config.helpers_only:
        direct_copies.extend(
            [
                (root / "scripts" / "mc_smoke_test.py", config.target_project / ".trellis" / "scripts" / "mc_smoke_test.py"),
                (root / "commands" / "claude" / "trellis" / "smoke-test.md", config.target_project / ".claude" / "commands" / "trellis" / "smoke-test.md"),
                (root / "commands" / "cursor" / "trellis-smoke-test.md", config.target_project / ".cursor" / "commands" / "trellis-smoke-test.md"),
            ]
        )

    replacements = {
        "__BASE_PACKAGE__": config.base_package,
        "__MOD_CLASS__": config.mod_class,
    }
    java_root = config.target_project / "src" / "main" / "java" / Path(*base_package_parts) / "smoketest"
    template_root = root / "loaders" / "forge" / "src" / "main" / "java" / "__BASE_PACKAGE_PATH__" / "smoketest"
    template_targets = [
        (template_root / "SmokeTestMarkers.java.template", java_root / "SmokeTestMarkers.java"),
        (template_root / "ServerSmokeTestHooks.java.template", java_root / "ServerSmokeTestHooks.java"),
        (template_root / "client" / "ClientSmokeTestHooks.java.template", java_root / "client" / "ClientSmokeTestHooks.java"),
    ]

    return InstallPlan(
        direct_copies=tuple(direct_copies),
        template_targets=tuple(template_targets),
    )


def install_files(config: InstallConfig) -> list[Path]:
    plan = build_install_plan(config)
    installed: list[Path] = []

    for source, target in plan.direct_copies:
        copy_file(source, target, config.force)
        installed.append(target)

    replacements = {
        "__BASE_PACKAGE__": config.base_package,
        "__MOD_CLASS__": config.mod_class,
    }
    for source, target in plan.template_targets:
        render_template(source, target, replacements, config.force)
        installed.append(target)

    return installed


def print_next_steps(config: InstallConfig) -> None:
    root = repo_root()
    print("\nNext steps:")
    print("1. Verify your main mod class exposes MODID.")
    if config.helpers_only:
        central_script = root / "scripts" / "mc_smoke_test.py"
        print("2. Run the central orchestration script in global Claude mode:")
        print(
            f'   python3 "{central_script}" --project-root "{config.target_project}" --task runServer --side server --bootstrap-helper'
        )
        print(
            f'   python3 "{central_script}" --project-root "{config.target_project}" --task runClient --side client --bootstrap-helper'
        )
    else:
        print("2. Run python3 ./.trellis/scripts/mc_smoke_test.py --task runServer --side server")
        print("3. Run python3 ./.trellis/scripts/mc_smoke_test.py --task runClient --side client")


def main() -> int:
    config = parse_args()
    installed = install_files(config)

    print("Installed Forge smoke-test kit:")
    print(f"- install_mode={config.install_mode}")
    for path in installed:
        try:
            display = path.relative_to(config.target_project)
        except ValueError:
            display = path
        print(f"- {display}")

    print_next_steps(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
