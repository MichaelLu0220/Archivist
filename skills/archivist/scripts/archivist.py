#!/usr/bin/env python3
"""Archivist: a tiny AGENTS.md gatekeeper for AI coding sessions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SECTIONS = [
    "Architecture Decisions",
    "Coding Style",
    "Workflow",
    "Tooling",
    "Project Rules",
]

ARCHIVIST_DIR = Path(".archivist")
ROOT_TEMPLATE_FILES = {
    "prompt.md": "prompt.md",
    "inbox.md": "inbox.md",
    "proposed.patch.md": "proposed.patch.md",
    "state.json": "state.json",
}
TEMPLATE_DIR = Path("templates") / "archivist"

TRIGGER_HEADING = "## Archivist 觸發規則"
ARCHIVIST_TRIGGER_BLOCK = """---

## Archivist 觸發規則

當使用者在對話中輸入 `Archivist sync`（或 `archivist sync`）時，這不是一般訊息，而是要求你執行「記憶歸檔」流程。若介面允許純文字 `@Archivist`，也可視為同一觸發；但在 Codex App 中優先使用 `Archivist sync`，避免 `@` 被解析成檔案或資料夾 mention。收到此觸發時，嚴格依照下列步驟進行：

1. 讀取 `.archivist/prompt.md`，那是你執行整理時要扮演的角色與規格。
2. 讀取 `.archivist/state.json`，了解上次同步的時間與狀態。
3. 把「自上次同步以來、目前你能看到的對話上下文中」值得長期保存的專案知識，整理寫入 `.archivist/inbox.md`（覆寫，不要累加舊內容）。
4. 依 `prompt.md` 的規格，比對 inbox、現有 AGENTS.md、state.json，產出條列式的「建議新增 / 修改 / 刪除 / 衝突」，寫入 `.archivist/proposed.patch.md` 作為暫存紀錄。
5. 把同一份 proposed.patch.md 內容貼到 chat 中，等待使用者在 chat 明確確認要接受哪幾項。**在使用者明確回覆前，絕不修改本 AGENTS.md。**
6. 使用者在 chat 確認後，只把被接受的項目套用到本檔對應章節，然後更新 state.json。

關鍵約束：寫入 AGENTS.md 永遠是流程的最後一步，且永遠需要使用者確認。寧可少記，不可亂記。
"""


@dataclass(frozen=True)
class Proposal:
    ordinal: int
    kind: str
    section: str | None
    target_index: int | None
    old: str | None
    new: str | None
    reason: str | None
    raw: str


class ArchivistError(Exception):
    pass


def read_text(path: Path) -> str:
    if not path.exists():
        raise ArchivistError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def repo_path(repo: Path, relative: str | Path) -> Path:
    return repo / relative


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_agents_text() -> str:
    parts = [
        "# Project Context",
        "",
        "<!-- This file is maintained by humans and Archivist. Archivist must never write here before user confirmation. -->",
        "",
    ]
    for section in SECTIONS:
        parts.extend([f"## {section}", "", ""])
    parts.append(ARCHIVIST_TRIGGER_BLOCK)
    return "\n".join(parts).rstrip() + "\n"


def ensure_default_agents(repo: Path) -> None:
    agents = repo_path(repo, "AGENTS.md")
    if not agents.exists():
        write_text(agents, default_agents_text())
        return

    text = read_text(agents).rstrip()
    additions: list[str] = []
    for section in SECTIONS:
        if not re.search(rf"^##\s+{re.escape(section)}\s*$", text, re.MULTILINE):
            additions.extend([f"## {section}", "", ""])
    if TRIGGER_HEADING not in text:
        additions.append(ARCHIVIST_TRIGGER_BLOCK)
    if additions:
        write_text(agents, text + "\n\n" + "\n".join(additions).rstrip() + "\n")


def embedded_template(target_name: str) -> str:
    if target_name == "state.json":
        return (
            json.dumps(
                {
                    "lastSyncedAt": None,
                    "lastAgentsMdHash": None,
                    "lastSummaryFile": None,
                    "_note": "首次執行時 lastSyncedAt 為 null。每次成功寫入 AGENTS.md 後更新此檔。",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
    if target_name == "inbox.md":
        return "<!-- Archivist inbox. 每次觸發 Archivist sync 時覆寫。 -->\n"
    if target_name == "proposed.patch.md":
        return "<!-- Archivist proposed patch. 每次觸發 Archivist sync 時覆寫。 -->\n"
    if target_name == "prompt.md":
        return "# Archivist\n\n維護 AGENTS.md。先在 chat 中提出建議，使用者確認前不要寫入 AGENTS.md。\n"
    return ""


def init_repo(repo: Path, force: bool = False, template_root: Path | None = None) -> None:
    ensure_default_agents(repo)
    target_dir = repo_path(repo, ARCHIVIST_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    for source_name, target_name in ROOT_TEMPLATE_FILES.items():
        source_roots = []
        if template_root is not None:
            source_roots.append(template_root / TEMPLATE_DIR)
            source_roots.append(template_root)
        source_roots.append(repo / TEMPLATE_DIR)
        source_roots.append(repo)
        target = target_dir / target_name
        if target.exists() and not force:
            continue
        source = next((root / source_name for root in source_roots if (root / source_name).exists()), None)
        if source is not None:
            shutil.copyfile(source, target)
            continue
        write_text(target, embedded_template(target_name))


def action_lines(text: str) -> list[str]:
    return [
        line.rstrip()
        for line in text.splitlines()
        if re.match(r"^\s*(?:\d+[\.)]\s*)?\[(?:ADD|MOD|DEL|!!)\]\s+[^/]", line)
    ]


def clean_item_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^\s*[-*]\s+", "", text)
    return text.strip()


def parse_proposals(text: str) -> list[Proposal]:
    proposals: list[Proposal] = []
    for raw in action_lines(text):
        line = re.sub(r"^\s*\d+[\.)]\s*", "", raw).strip()
        ordinal = len(proposals) + 1

        add_match = re.match(r"^\[ADD\]\s+(.+?)\s*→\s*(.+)$", line)
        if add_match:
            proposals.append(
                Proposal(
                    ordinal,
                    "ADD",
                    add_match.group(1).strip(),
                    None,
                    None,
                    clean_item_text(add_match.group(2)),
                    None,
                    raw,
                )
            )
            continue

        mod_match = re.match(r"^\[MOD\]\s+(.+?)\s+#(\d+):\s*(.+?)\s*→\s*(.+)$", line)
        if mod_match:
            proposals.append(
                Proposal(
                    ordinal,
                    "MOD",
                    mod_match.group(1).strip(),
                    int(mod_match.group(2)),
                    clean_item_text(mod_match.group(3)),
                    clean_item_text(mod_match.group(4)),
                    None,
                    raw,
                )
            )
            continue

        del_match = re.match(r"^\[DEL\]\s+(.+?)\s+#(\d+):\s*(.+?)(?:\s*←\s*(.+))?$", line)
        if del_match:
            proposals.append(
                Proposal(
                    ordinal,
                    "DEL",
                    del_match.group(1).strip(),
                    int(del_match.group(2)),
                    clean_item_text(del_match.group(3)),
                    None,
                    del_match.group(4).strip() if del_match.group(4) else None,
                    raw,
                )
            )
            continue

        conflict_match = re.match(r"^\[!!\]\s+(.+?)\s+#(\d+)\s+與本次衝突：(.+)$", line)
        if conflict_match:
            proposals.append(
                Proposal(
                    ordinal,
                    "!!",
                    conflict_match.group(1).strip(),
                    int(conflict_match.group(2)),
                    conflict_match.group(3).strip(),
                    None,
                    "conflict",
                    raw,
                )
            )
            continue

        raise ArchivistError(f"cannot parse proposal line: {raw}")
    return proposals


def parse_selection(selection: str, max_ordinal: int) -> set[int]:
    value = selection.strip().lower()
    if value == "all":
        return set(range(1, max_ordinal + 1))
    if value == "none":
        return set()
    if not value:
        raise ArchivistError("empty selection")

    selected: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        range_match = re.match(r"^(\d+)-(\d+)$", part)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            if start > end:
                raise ArchivistError(f"invalid range: {part}")
            selected.update(range(start, end + 1))
            continue
        if not part.isdigit():
            raise ArchivistError(f"invalid selection token: {part}")
        selected.add(int(part))

    invalid = sorted(n for n in selected if n < 1 or n > max_ordinal)
    if invalid:
        raise ArchivistError(f"selection out of range: {', '.join(map(str, invalid))}")
    return selected


def section_bounds(lines: list[str], section: str) -> tuple[int, int]:
    heading = f"## {section}"
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index
            break
    if start is None:
        raise ArchivistError(f"AGENTS.md is missing section: {section}")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("## ") or stripped == "---":
            end = index
            break
    return start, end


def section_item_lines(lines: list[str], section: str) -> list[int]:
    start, end = section_bounds(lines, section)
    item_lines: list[int] = []
    in_comment = False
    for index in range(start + 1, end):
        stripped = lines[index].strip()
        if stripped.startswith("<!--"):
            in_comment = True
        if not stripped or in_comment:
            if stripped.endswith("-->"):
                in_comment = False
            continue
        if stripped.endswith("-->"):
            in_comment = False
            continue
        item_lines.append(index)
    return item_lines


def normalize_section(section: str) -> str:
    for allowed in SECTIONS:
        if section.strip().lower() == allowed.lower():
            return allowed
    raise ArchivistError(f"unknown AGENTS.md section: {section}")


def insert_item(lines: list[str], section: str, content: str) -> None:
    start, end = section_bounds(lines, section)
    item_indexes = section_item_lines(lines, section)
    insert_at = item_indexes[-1] + 1 if item_indexes else start + 1

    if not item_indexes:
        while insert_at < end and (
            not lines[insert_at].strip()
            or lines[insert_at].strip().startswith("<!--")
            or lines[insert_at].strip().endswith("-->")
        ):
            insert_at += 1
    lines.insert(insert_at, f"- {content}")

    if insert_at + 1 < len(lines) and lines[insert_at + 1].strip():
        lines.insert(insert_at + 1, "")


def replace_item(lines: list[str], section: str, target_index: int, content: str) -> None:
    item_indexes = section_item_lines(lines, section)
    if target_index < 1 or target_index > len(item_indexes):
        raise ArchivistError(f"{section} has no item #{target_index}")
    lines[item_indexes[target_index - 1]] = f"- {content}"


def delete_item(lines: list[str], section: str, target_index: int) -> None:
    item_indexes = section_item_lines(lines, section)
    if target_index < 1 or target_index > len(item_indexes):
        raise ArchivistError(f"{section} has no item #{target_index}")
    del lines[item_indexes[target_index - 1]]


def apply_proposals(agents_text: str, proposals: list[Proposal], selected: set[int]) -> tuple[str, list[str]]:
    lines = agents_text.splitlines()
    applied: list[str] = []
    selected_proposals = [proposal for proposal in proposals if proposal.ordinal in selected]

    for proposal in selected_proposals:
        if proposal.kind == "!!":
            applied.append(f"skipped #{proposal.ordinal} ([!!] requires manual decision)")

    for proposal in selected_proposals:
        if proposal.kind != "MOD":
            continue
        if proposal.section is None or proposal.target_index is None or proposal.new is None:
            raise ArchivistError(f"proposal #{proposal.ordinal} is incomplete")
        section = normalize_section(proposal.section)
        replace_item(lines, section, proposal.target_index, proposal.new)
        applied.append(f"applied #{proposal.ordinal} MOD {section} #{proposal.target_index}")

    delete_proposals = sorted(
        (proposal for proposal in selected_proposals if proposal.kind == "DEL"),
        key=lambda proposal: (normalize_section(proposal.section or ""), proposal.target_index or 0),
        reverse=True,
    )
    for proposal in delete_proposals:
        if proposal.section is None or proposal.target_index is None:
            raise ArchivistError(f"proposal #{proposal.ordinal} is incomplete")
        section = normalize_section(proposal.section)
        delete_item(lines, section, proposal.target_index)
        applied.append(f"applied #{proposal.ordinal} DEL {section} #{proposal.target_index}")

    for proposal in selected_proposals:
        if proposal.kind != "ADD":
            continue
        if proposal.section is None:
            raise ArchivistError(f"proposal #{proposal.ordinal} has no section")
        section = normalize_section(proposal.section)
        if proposal.new is None:
            raise ArchivistError(f"proposal #{proposal.ordinal} has no new content")
        insert_item(lines, section, proposal.new)
        applied.append(f"applied #{proposal.ordinal} ADD {section}")

    return "\n".join(lines).rstrip() + "\n", applied


def update_state(repo: Path, agents_text: str) -> None:
    state_path = repo_path(repo, ARCHIVIST_DIR / "state.json")
    if state_path.exists():
        try:
            state = json.loads(read_text(state_path))
        except json.JSONDecodeError:
            state = {}
    else:
        state = {}
    state["lastSyncedAt"] = now_iso()
    state["lastAgentsMdHash"] = sha256_text(agents_text)
    state.setdefault("lastSummaryFile", None)
    write_text(state_path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def command_init(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    init_repo(repo, force=args.force)
    print(f"initialized Archivist files in {repo}")
    return 0


def command_install(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    if not target.exists():
        raise ArchivistError(f"target repo does not exist: {target}")
    if not target.is_dir():
        raise ArchivistError(f"target is not a directory: {target}")

    source_root = Path(__file__).resolve().parent
    init_repo(target, force=args.force, template_root=source_root)

    source_cli = source_root / Path(__file__).name
    target_cli = target / "archivist.py"
    if source_cli.resolve() != target_cli.resolve():
        if target_cli.exists() and not args.force:
            print(f"kept existing {target_cli}")
        else:
            shutil.copyfile(source_cli, target_cli)
            print(f"installed {target_cli}")

    print(f"installed Codex Archivist files in {target}")
    print("open that repo in Codex App and type 'Archivist sync' when you want to archive project memory")
    return 0


def command_show(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    proposed = repo_path(repo, ARCHIVIST_DIR / "proposed.patch.md")
    if not proposed.exists():
        proposed = repo_path(repo, "proposed.patch.md")
    text = read_text(proposed)
    proposals = parse_proposals(text)
    if not proposals:
        print(text.rstrip() or "no proposals")
        return 0
    for proposal in proposals:
        print(f"{proposal.ordinal}. {proposal.raw}")
    return 0


def command_apply(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    agents_path = repo_path(repo, "AGENTS.md")
    proposed_path = repo_path(repo, ARCHIVIST_DIR / "proposed.patch.md")
    if not proposed_path.exists():
        proposed_path = repo_path(repo, "proposed.patch.md")

    proposals = parse_proposals(read_text(proposed_path))
    if not proposals:
        print("no actionable proposals")
        return 0

    selected = parse_selection(args.selection, len(proposals))
    if not selected:
        print("no proposals selected")
        return 0

    new_agents, applied = apply_proposals(read_text(agents_path), proposals, selected)
    if not args.dry_run:
        write_text(agents_path, new_agents)
        init_repo(repo, force=False)
        update_state(repo, new_agents)

    for line in applied:
        print(line)
    if args.dry_run:
        print("dry run: AGENTS.md and state.json were not changed")
    return 0


def command_check(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    errors: list[str] = []
    for relative in ["AGENTS.md", ARCHIVIST_DIR / "prompt.md", ARCHIVIST_DIR / "state.json"]:
        if not repo_path(repo, relative).exists():
            errors.append(f"missing {relative}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    agents_text = read_text(repo_path(repo, "AGENTS.md"))
    for section in SECTIONS:
        try:
            section_bounds(agents_text.splitlines(), section)
        except ArchivistError as exc:
            errors.append(str(exc))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Archivist workspace looks ready")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Maintain AGENTS.md through confirmed Archivist proposals.")
    parser.add_argument("--repo", default=".", help="repository root (default: current directory)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create .archivist files")
    init_parser.add_argument("--force", action="store_true", help="overwrite existing .archivist files")
    init_parser.set_defaults(func=command_init)

    install_parser = subparsers.add_parser("install", help="install Archivist into a Codex project")
    install_parser.add_argument("target", help="target repository root")
    install_parser.add_argument("--force", action="store_true", help="overwrite existing Archivist files in the target")
    install_parser.set_defaults(func=command_install)

    show_parser = subparsers.add_parser("show", help="print numbered proposed.patch.md items")
    show_parser.set_defaults(func=command_show)

    apply_parser = subparsers.add_parser("apply", help="apply accepted proposal numbers to AGENTS.md")
    apply_parser.add_argument("selection", help="all, none, 1,3, or ranges like 1-4")
    apply_parser.add_argument("--dry-run", action="store_true", help="validate without writing files")
    apply_parser.set_defaults(func=command_apply)

    check_parser = subparsers.add_parser("check", help="validate Archivist workspace files")
    check_parser.set_defaults(func=command_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ArchivistError as exc:
        print(f"archivist: {exc}", file=sys.stderr)
        return 1
    except PermissionError as exc:
        print(f"archivist: permission denied while writing {exc.filename}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
