# Contributing

Thanks for helping improve Archivist.

Archivist is intentionally narrow: it helps Codex maintain durable project memory in `AGENTS.md` with chat-first human confirmation. Contributions should preserve that focus.

## Good First Contributions

- Improve installation instructions for a specific OS or shell.
- Add a small before-and-after example.
- Improve error messages in the helper CLI.
- Add tests for proposal parsing or conflict handling.
- Clarify documentation where first-time users may get stuck.

## Development Setup

Clone the repository:

```bash
git clone https://github.com/MichaelLu0220/Archivist.git
cd Archivist
```

Run tests:

```bash
python -m unittest discover -s tests
```

Root `archivist.py` is local-only. Public helper code lives at:

```text
skills/archivist/scripts/archivist.py
```

## Pull Requests

Before opening a pull request:

- Keep changes scoped to one concern.
- Add or update tests when behavior changes.
- Update `README.md` when user-facing behavior changes.
- Do not commit `.archivist/`, `.codex/`, root `AGENTS.md`, or root `archivist.py`.

## Project Boundaries

Archivist should remain:

- A Codex skill first.
- A small helper CLI second.
- A gatekeeper for `AGENTS.md`, not a general note-taking tool.

Please avoid adding UI, marketplace behavior, or multi-agent orchestration unless the project direction explicitly changes.

