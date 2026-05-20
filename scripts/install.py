#!/usr/bin/env python3
"""Install the Archivist Codex skill and optionally initialize a repo."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def copytree_replace(source: Path, target: Path, force: bool) -> None:
    if target.exists():
        if not force:
            print(f"kept existing {target}")
            return
        shutil.rmtree(target)
    shutil.copytree(source, target)
    print(f"installed {target}")


def run_repo_init(root: Path, repo: Path, force: bool) -> None:
    command = [sys.executable, str(root / "archivist.py"), "install", str(repo)]
    if force:
        command.append("--force")
    subprocess.run(command, check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install Archivist for Codex App.")
    parser.add_argument(
        "--codex-home",
        default=str(Path.home() / ".codex"),
        help="Codex home directory (default: ~/.codex)",
    )
    parser.add_argument(
        "--init-repo",
        help="optional repository root to initialize with .archivist files and archivist.py",
    )
    parser.add_argument("--force", action="store_true", help="overwrite existing installed skill/files")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    skill_source = root / "skills" / "archivist"
    if not skill_source.exists():
        raise SystemExit(f"missing skill source: {skill_source}")

    codex_home = Path(args.codex_home).expanduser().resolve()
    skill_target = codex_home / "skills" / "archivist"
    skill_target.parent.mkdir(parents=True, exist_ok=True)
    copytree_replace(skill_source, skill_target, force=args.force)

    if args.init_repo:
        repo = Path(args.init_repo).expanduser().resolve()
        if not repo.exists():
            raise SystemExit(f"target repo does not exist: {repo}")
        run_repo_init(root, repo, args.force)

    print("\nNext:")
    print("1. Restart Codex App or open a new chat.")
    print("2. Run /Archivist, $archivist, or Archivist sync in a repo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
