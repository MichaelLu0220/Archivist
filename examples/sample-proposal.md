# Sample Archivist Proposal

```text
1. [ADD] Workflow → Mirror proposals to .archivist/proposed.patch.md as a temporary audit copy
2. [MOD] Tooling #1: Use Python for the helper CLI → Use a single-file Python standard-library helper CLI
3. [ADD] Project Rules → Do not auto-apply [!!] conflict items

Accept which items? (examples: 1,3 / all / none / item number + edited text)
```

If the user replies:

```text
all
```

Archivist applies only the accepted items to `AGENTS.md`.
