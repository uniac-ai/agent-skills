import tempfile
import unittest
from pathlib import Path

from validate import validate_links


class MarkdownLinksTest(unittest.TestCase):
    def validate(self, files: dict[str, str]) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            skill = root / "skill"
            skill.mkdir()
            for name, text in files.items():
                path = skill / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            return validate_links(skill, root)

    def test_shared_child_is_acyclic(self):
        self.assertEqual(self.validate({
            "SKILL.md": "[a](a.md) [b](b.md)",
            "a.md": "[leaf](leaf.md)",
            "b.md": "[leaf](leaf.md#detail)",
            "leaf.md": "# Detail",
        }), [])

    def test_anchors_external_links_and_code_are_not_dependencies(self):
        self.assertEqual(self.validate({
            "SKILL.md": (
                "[local](#detail) [same file](./SKILL.md#detail) "
                "[web](https://example.com/missing.md) "
                "[relative web](//example.com/missing.md) "
                "[mail](mailto:help@example.com) "
                "`[inline](missing.md)`\n```md\n[fenced](missing.md)\n```"
            ),
        }), [])

    def test_cycles_report_the_closed_path(self):
        for names in [("a.md",), ("a.md", "b.md"), ("a.md", "b.md", "c.md")]:
            with self.subTest(names=names):
                files = {
                    name: f"[next]({names[(index + 1) % len(names)]})"
                    for index, name in enumerate(names)
                }
                chain = " -> ".join(f"skill/{name}" for name in (*names, names[0]))
                self.assertEqual(self.validate(files), [f"cyclic Markdown links: {chain}"])

    def test_missing_and_outside_links_still_fail(self):
        defects = self.validate({
            "SKILL.md": "[missing](missing.md#detail) [outside](../outside.md)",
            "../outside.md": "Outside the skill.",
        })
        self.assertEqual(defects, [
            "skill/SKILL.md: broken link 'missing.md#detail'",
            "skill/SKILL.md: link '../outside.md' escapes the skill",
        ])


if __name__ == "__main__":
    unittest.main()
