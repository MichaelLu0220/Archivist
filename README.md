# Archivist

Archivist is a Codex skill for maintaining durable project memory in `AGENTS.md`.

It is deliberately small: no UI, no marketplace, no multi-agent system. Its job is to help Codex decide which project decisions are worth saving, propose concise changes in chat, and only update `AGENTS.md` after explicit human confirmation.

## What It Does

- Reads visible project context and existing `AGENTS.md` rules.
- Filters for durable knowledge: architecture decisions, coding style, workflow, tooling, and project-specific constraints.
- Writes proposed changes as `[ADD]`, `[MOD]`, `[DEL]`, or `[!!]`.
- Requires chat confirmation before changing `AGENTS.md`.
- Keeps runtime state in `.archivist/`, which should stay local and git ignored.

## Repository Layout

```text
README.md                                  Project overview and setup
scripts/install.py                         Installs the Codex skill
skills/archivist/SKILL.md                  Codex skill entrypoint
skills/archivist/references/workflow.md    Detailed archival rules
skills/archivist/scripts/archivist.py      Helper CLI used by the skill
templates/archivist/                       Initial .archivist runtime templates
tests/                                     Unit tests for the helper CLI
```

Local-only files such as root `AGENTS.md`, root `archivist.py`, `.archivist/`, `.codex/`, and draft notes are intentionally excluded from Git.

## Install For Codex App

Fast path for Windows PowerShell:

```powershell
$dir = Join-Path $env:TEMP "Archivist"; if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }; git clone https://github.com/MichaelLu0220/Archivist.git $dir; python "$dir\scripts\install.py"
```

Then restart Codex App or open a new chat. Trigger Archivist with one of:

```text
/Archivist
$archivist
Archivist sync
```

`Archivist sync` is the safest plain-text fallback in Codex App, because `@Archivist` may be parsed as a file or folder mention.

Developer install:

```bash
git clone https://github.com/MichaelLu0220/Archivist.git
cd Archivist
python scripts/install.py
```

On Windows, if `python` is not on `PATH`, use your installed Python executable path.

To initialize the current repo at the same time:

```powershell
$repo = (Get-Location).Path; $dir = Join-Path $env:TEMP "Archivist"; if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }; git clone https://github.com/MichaelLu0220/Archivist.git $dir; python "$dir\scripts\install.py" --init-repo "$repo"
```

## Optional: Initialize A Target Repo

After `python scripts/install.py`, the Archivist skill is globally available in Codex App. The one-line PowerShell command above already runs that installer for you.

This extra step is only needed if you want to prepare a specific repository with repo-local runtime files and the helper CLI ahead of time:

```bash
python scripts/install.py --init-repo /path/to/target/repo
```

This creates:

```text
.archivist/prompt.md
.archivist/inbox.md
.archivist/proposed.patch.md
.archivist/state.json
archivist.py
```

It also appends the Archivist trigger instructions to the target repo's `AGENTS.md` when needed.

The generated `.archivist/` directory is runtime state and should be git ignored in the target repo.

## Workflow

1. Start a Codex chat in a repo that has Archivist installed.
2. Run `Archivist sync`.
3. Archivist reviews visible conversation context since the last sync.
4. It proposes numbered changes in chat and mirrors them to `.archivist/proposed.patch.md`.
5. You confirm accepted items in chat, for example `1,3`, `all`, or `none`.
6. Only confirmed items are applied to `AGENTS.md`.

Conflict items marked `[!!]` are never auto-applied. They require a human decision.

## Helper CLI

Run the helper directly when you need to inspect or apply proposals:

```bash
python skills/archivist/scripts/archivist.py --repo /path/to/repo show
python skills/archivist/scripts/archivist.py --repo /path/to/repo apply 1,3
python skills/archivist/scripts/archivist.py --repo /path/to/repo apply all
python skills/archivist/scripts/archivist.py --repo /path/to/repo apply 1-4 --dry-run
python skills/archivist/scripts/archivist.py --repo /path/to/repo check
```

Available commands:

- `init`: create `.archivist` files in the current repo.
- `install <target>`: install Archivist into a target repo.
- `show`: print numbered proposal items.
- `apply <selection>`: apply accepted proposals to `AGENTS.md`.
- `check`: validate Archivist workspace files.

## Proposal Format

Archivist proposals use this shape:

```text
1. [ADD] <Section> → <concise content>
2. [MOD] <Section> #<existing item number>: <old> → <new>
3. [DEL] <Section> #<existing item number>: <content> ← <short reason>
4. [!!] <Section> #<existing item number> conflict: existing "<old>" vs new "<new>"
```

Supported `AGENTS.md` sections:

- `Architecture Decisions`
- `Coding Style`
- `Workflow`
- `Tooling`
- `Project Rules`

## Tests

Run:

```bash
python -m unittest discover -s tests
```

Tests import the tracked helper from `skills/archivist/scripts`; root `archivist.py` is local-only and not required.
