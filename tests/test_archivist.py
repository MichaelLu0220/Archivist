import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from archivist import TRIGGER_HEADING, apply_proposals, init_repo, parse_proposals, parse_selection


AGENTS = """# Project Context

## Architecture Decisions

- Keep docs lightweight
- Use AGENTS.md as the durable memory file
- Avoid marketplace scope

## Coding Style

## Workflow

## Tooling

## Project Rules

"""


class ArchivistTests(unittest.TestCase):
    def test_parse_selection_supports_all_lists_and_ranges(self):
        self.assertEqual(parse_selection("all", 3), {1, 2, 3})
        self.assertEqual(parse_selection("1,3", 3), {1, 3})
        self.assertEqual(parse_selection("1-3", 4), {1, 2, 3})

    def test_apply_add_mod_and_descending_delete(self):
        proposals = parse_proposals(
            "\n".join(
                [
                    "[DEL] Architecture Decisions #1: Keep docs lightweight ← folded into README",
                    "[DEL] Architecture Decisions #2: Use AGENTS.md as the durable memory file ← obsolete",
                    "[MOD] Architecture Decisions #3: Avoid marketplace scope → Do not build marketplace scope",
                    "[ADD] Project Rules → Require human confirmation before writing AGENTS.md",
                ]
            )
        )

        result, applied = apply_proposals(AGENTS, proposals, {1, 2, 3, 4})

        self.assertIn("- Do not build marketplace scope", result)
        self.assertIn("- Require human confirmation before writing AGENTS.md", result)
        self.assertNotIn("- Keep docs lightweight", result)
        self.assertNotIn("- Use AGENTS.md as the durable memory file", result)
        self.assertEqual(len(applied), 4)

    def test_conflict_is_not_auto_applied(self):
        proposals = parse_proposals(
            "[!!] Architecture Decisions #1 與本次衝突：現有「Keep docs lightweight」 vs inbox「Add UI」"
        )

        result, applied = apply_proposals(AGENTS, proposals, {1})

        self.assertEqual(result, AGENTS.rstrip() + "\n")
        self.assertEqual(applied, ["skipped #1 ([!!] requires manual decision)"])

    def test_init_repo_preserves_existing_agents_and_adds_trigger(self):
        with TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "AGENTS.md").write_text("# Existing Rules\n\nKeep this.\n", encoding="utf-8")

            init_repo(repo, template_root=Path.cwd())

            agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Keep this.", agents)
            self.assertIn("## Architecture Decisions", agents)
            self.assertIn(TRIGGER_HEADING, agents)
            self.assertTrue((repo / ".archivist" / "prompt.md").exists())


if __name__ == "__main__":
    unittest.main()
