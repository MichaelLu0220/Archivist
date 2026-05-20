---
name: archivist
description: Archive durable project memory into AGENTS.md with chat-first human confirmation. Use when the user asks to archive project memory, update AGENTS.md from conversation context, run "Archivist sync", organize long-term project knowledge, audit AGENTS.md for stale or conflicting rules, or decide whether chat decisions should be saved for future AI coding sessions. If invoked through /Archivist, $archivist, or the skill picker, immediately run the archival workflow; do not reply that the skill is ready. In Codex App, do not rely on @Archivist because @ may become a file or folder mention.
---

# Archivist

Maintain `AGENTS.md` as compact repo memory. Act as a gatekeeper, not a recorder.

## Run

1. Read `AGENTS.md` and `.archivist/state.json` if present.
2. Review visible conversation context since the last sync as best as possible; mention if context may be incomplete.
3. Read `references/workflow.md` for filtering, proposal format, conflict, deletion, and safety rules.
4. Propose changes in chat first. If filesystem access is available, mirror the proposal to `.archivist/proposed.patch.md`.
5. Wait for explicit chat confirmation before writing `AGENTS.md`.
6. After confirmation, apply only accepted items and update `.archivist/state.json`.

## Runtime Files

- `.archivist/state.json`: last sync metadata and `AGENTS.md` hash.
- `.archivist/inbox.md`: optional scratch summary of visible conversation material.
- `.archivist/proposed.patch.md`: temporary audit copy of the chat proposal.

The confirmation interface is always chat; `.archivist/proposed.patch.md` is not the confirmation interface.

## Helper

After user confirmation, prefer a repo-local `archivist.py` if present. Otherwise use `scripts/archivist.py`:

```bash
python scripts/archivist.py --repo /path/to/repo apply 1,3
python scripts/archivist.py --repo /path/to/repo apply all
```
