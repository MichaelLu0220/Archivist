# Archivist Workflow Reference

## Durable Knowledge

Archive only long-term project knowledge:

- Architecture decisions
- Coding style
- Repeatable workflow preferences
- Tooling and environment conventions
- Project rules and constraints

Filter out one-off Q&A, temporary debugging details, jokes, emotional chat, casual conversation, unresolved brainstorming, and generic knowledge not specific to the project.

## AGENTS.md Schema

Use only these sections:

- `Architecture Decisions`
- `Coding Style`
- `Workflow`
- `Tooling`
- `Project Rules`

If sections are missing, include section creation in the proposal or create them only after confirmation.

## Compression Rules

- One saved rule per line.
- Use imperative or noun-phrase style.
- Keep entries extremely concise.
- Put short reasons in parentheses only when useful.
- Never paste raw conversation text.
- Prefer `Use Jotai for state management` over `We decided that from now on we will use Jotai for state management`.

## Proposal Format

Show numbered items in chat using exactly this format:

```text
1. [ADD] <Section> → <concise content>
2. [MOD] <Section> #<existing item number>: <old> → <new>
3. [DEL] <Section> #<existing item number>: <content> ← <short reason>
4. [!!] <Section> #<existing item number> conflict: existing "<old>" vs new "<new>"
```

End every proposal list with:

```text
Accept which items? (examples: 1,3 / all / none / item number + edited text)
```

If no changes are worth archiving, say:

```text
No archival changes recommended.
```

## Conflict And Deletion Rules

- Mark contradictions as `[!!]` unless the user explicitly said to replace the old rule.
- Do not auto-apply `[!!]` items.
- Use `[MOD]` when the user explicitly says an existing rule changed.
- Every sync should scan existing `AGENTS.md` for stale, duplicate, low-value, or overly verbose entries.
- Suggest `[DEL]` for entries that should be removed to keep `AGENTS.md` small.

## Safety Rules

- Never write `AGENTS.md` before explicit chat confirmation.
- Be conservative. When unsure whether something is durable project knowledge, do not archive it.
- Do not create UI, marketplace behavior, or multi-agent workflows. Archivist has one job: guard `AGENTS.md`.
- If a helper fails, inspect resulting files before retrying to avoid duplicate entries.
