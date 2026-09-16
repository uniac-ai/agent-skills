import tempfile
import unittest
from pathlib import Path

from validate import parse_frontmatter, validate_links


class LinksTest(unittest.TestCase):
    def validate(self, files: dict[str, str]) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for name, text in files.items():
                path = root / "skills" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            return validate_links(sorted((root / "skills").iterdir()), root, offline=True)

    def test_local_links_docs_markdown_urls_anchors_and_code_pass(self):
        self.assertEqual(self.validate({
            "uniac/SKILL.md": "[ref](references/platform.md#volumes) [self](#model) "
                              "[page](https://docs.uniac.ai/resources/service.md#public-endpoints) "
                              "[corpus](https://docs.uniac.ai/llms-full.txt) [site](https://uniac.ai) "
                              "`[code](/kept)`\n```yaml\n[fenced](/kept)\n```\n",
            "uniac/references/platform.md": "# Platform\n",
        }), [])

    def test_each_defect_is_named(self):
        self.assertEqual(self.validate({
            "uniac/SKILL.md": "[gone](references/missing.md) [out](../other/SKILL.md) "
                              "[route](/resources/service) [html](https://docs.uniac.ai/resources/service)\n",
            "other/SKILL.md": "# Other\n",
        }), [
            "skills/uniac/SKILL.md: broken link 'references/missing.md'",
            "skills/uniac/SKILL.md: link '../other/SKILL.md' escapes the skill",
            "skills/uniac/SKILL.md: site route '/resources/service'; skills are read as files",
            "skills/uniac/SKILL.md: 'https://docs.uniac.ai/resources/service' is a page URL; link the page's Markdown (.md)",
        ])


class FrontmatterTest(unittest.TestCase):
    def test_strict_scalars(self):
        defects = []
        fields = parse_frontmatter('---\nname: uniac\ndescription: "Deploy: fast"\n---\n', defects, "x")
        self.assertEqual((fields, defects), ({"name": "uniac", "description": "Deploy: fast"}, []))
        parse_frontmatter("---\nname: uniac\ndescription: Deploy: fast\n---\n", defects, "x")
        self.assertEqual(len(defects), 1)


if __name__ == "__main__":
    unittest.main()
