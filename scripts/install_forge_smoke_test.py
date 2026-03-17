from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
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
        "--force",
        action="store_true",
        help="Overwrite existing target files.",
    )
    return parser.parse_args()


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


def install_files(target_project: Path, base_package: str, mod_class: str, force: bool) -> list[Path]:
    root = repo_root()
    base_package_parts = validate_base_package(base_package)
    validate_mod_class(mod_class)

    installed: list[Path] = []

    direct_copies = [
        (root / "scripts" / "mc_smoke_test.py", target_project / ".trellis" / "scripts" / "mc_smoke_test.py"),
        (root / "commands" / "claude" / "trellis" / "smoke-test.md", target_project / ".claude" / "commands" / "trellis" / "smoke-test.md"),
        (root / "commands" / "cursor" / "trellis-smoke-test.md", target_project / ".cursor" / "commands" / "trellis-smoke-test.md"),
    ]

    for source, target in direct_copies:
        copy_file(source, target, force)
        installed.append(target)

    replacements = {
        "__BASE_PACKAGE__": base_package,
        "__MOD_CLASS__": mod_class,
    }
    java_root = target_project / "src" / "main" / "java" / Path(*base_package_parts) / "smoketest"
    template_root = root / "loaders" / "forge" / "src" / "main" / "java" / "__BASE_PACKAGE_PATH__" / "smoketest"

    template_targets = [
        (template_root / "SmokeTestMarkers.java.template", java_root / "SmokeTestMarkers.java"),
        (template_root / "ServerSmokeTestHooks.java.template", java_root / "ServerSmokeTestHooks.java"),
        (template_root / "client" / "ClientSmokeTestHooks.java.template", java_root / "client" / "ClientSmokeTestHooks.java"),
    ]

    for source, target in template_targets:
        render_template(source, target, replacements, force)
        installed.append(target)

    return installed


def main() -> int:
    args = parse_args()
    target_project = Path(args.target_project).resolve()
    if not target_project.exists():
        raise SystemExit(f"Target project does not exist: {target_project}")

    installed = install_files(
        target_project=target_project,
        base_package=args.base_package,
        mod_class=args.mod_class,
        force=args.force,
    )

    print("Installed Forge smoke-test kit:")
    for path in installed:
        try:
            display = path.relative_to(target_project)
        except ValueError:
            display = path
        print(f"- {display}")

    print("\nNext steps:")
    print("1. Verify your main mod class exposes MODID.")
    print("2. Run python3 ./.trellis/scripts/mc_smoke_test.py --task runServer --side server")
    print("3. Run python3 ./.trellis/scripts/mc_smoke_test.py --task runClient --side client")
    return 0


if __name__ == "__main__":
    sys.exit(main())
