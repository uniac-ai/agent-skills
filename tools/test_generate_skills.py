import json
import tempfile
import unittest
from pathlib import Path

from generate_skills import expected, generate

NAVIGATION = {"navigation": {"groups": [
    {"group": "Uniac", "pages": ["index", {"group": "Composition", "pages": ["composition/yaml"]},
                                 {"group": "CLI", "root": "cli/overview", "pages": []}]},
    {"group": "Guides", "pages": ["setup", "quickstart"]},
]}}

PAGES = {
    "docs/docs.json": json.dumps(NAVIGATION),
    "docs/index.mdx": '---\ntitle: "How Uniac works"\ndescription: "Services run in a project."\n---\n\n'
                      "Services run in a [project](/composition/yaml#declarations) described in YAML.\n",
    "docs/composition/yaml.mdx": "---\ntitle: Composition in YAML\n---\n\n"
                                 "[system](/) [cli](/cli/overview) [quickstart](/quickstart) "
                                 "[section](#declarations) [external](https://example.com/page.md)\n\n## Declarations\n",
    "docs/cli/overview.mdx": '---\ntitle: "Uniac CLI"\ndescription: "Run commands."\n---\n\nRun `uniac plan`.\n',
    "docs/setup.mdx": '---\ntitle: "Set up Uniac"\ndescription: "Install the CLI."\n---\n\n'
                      "Install, then read [authentication](/cli/overview#auth) and the "
                      "[skill](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/SKILL.md).\n",
    "docs/quickstart.mdx": '---\ntitle: "Uniac quickstart"\ndescription: "Deploy an app."\n---\n\n'
                           "## Example\n\nDeploy with [the CLI](/cli/overview) after [setup](/setup).\n",
    "skills/uniac/SKILL.md": "---\nname: uniac\ndescription: Knowledge.\n---\n\n# Uniac\n\n"
                             "[system](references/overview.md) [yaml](references/composition/yaml.md#declarations) "
                             "[quickstart](https://docs.uniac.ai/quickstart.md)\n",
}


class GenerateSkillsTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        for name, text in PAGES.items():
            self.write(name, text)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def snapshot(self):
        return {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}

    def test_reference_pages_become_headed_files_linked_within_the_skill(self):
        files = expected(self.root)
        self.assertEqual(files[Path("skills/uniac/references/overview.md")],
                         "# How Uniac works\n\nServices run in a [project](composition/yaml.md#declarations) described in YAML.\n")
        self.assertEqual(files[Path("skills/uniac/references/composition/yaml.md")],
                         "# Composition in YAML\n\n[system](../overview.md) [cli](../cli/overview.md) "
                         "[quickstart](https://docs.uniac.ai/quickstart.md) [section](#declarations) "
                         "[external](https://example.com/page.md)\n\n## Declarations\n")

    def test_guides_become_a_skill_and_the_setup_document_linked_to_the_site(self):
        files = expected(self.root)
        quickstart = files[Path("skills/uniac-quickstart/SKILL.md")]
        self.assertEqual(quickstart, "---\nname: uniac-quickstart\ndescription: Deploy an app.\n---\n\n"
                                     "# Uniac quickstart\n\n## Example\n\nDeploy with [the CLI](https://docs.uniac.ai/cli/overview.md) "
                                     "after [setup](https://docs.uniac.ai/setup.md).\n")
        self.assertEqual(files[Path("agents/agents.md")],
                         "# Set up Uniac\n\nInstall, then read [authentication](https://docs.uniac.ai/cli/overview.md#auth) and the "
                         "[skill](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/SKILL.md).\n")

    def test_the_site_serves_each_skill_entry_with_site_links(self):
        files = expected(self.root)
        self.assertEqual(files[Path("docs/.mintlify/skills/uniac/SKILL.md")],
                         "---\nname: uniac\ndescription: Knowledge.\n---\n\n# Uniac\n\n"
                         "[system](https://docs.uniac.ai/index.md) [yaml](https://docs.uniac.ai/composition/yaml.md#declarations) "
                         "[quickstart](https://docs.uniac.ai/quickstart.md)\n")
        self.assertEqual(files[Path("docs/.mintlify/skills/uniac-quickstart/SKILL.md")],
                         files[Path("skills/uniac-quickstart/SKILL.md")])

    def test_code_is_byte_for_byte_while_entities_decode_in_prose(self):
        code = ["`[link](/missing) &lt;kept>`", '```yaml\nvalue: "${{api.host}}"\nlink: "[x](/missing)"\n```\n']
        self.write("docs/cli/overview.mdx", '---\ntitle: "CLI"\n---\n\nA &lt;name> with &#123;braces&#125;.\n\n' + "\n\n".join(code))
        result = expected(self.root)[Path("skills/uniac/references/cli/overview.md")]
        self.assertIn("A <name> with {braces}.", result)
        for block in code:
            self.assertIn(block, result)

    def test_check_reports_drift_missing_and_stale_files_without_writing(self):
        self.assertNotEqual(generate(self.root), [])
        self.assertEqual(generate(self.root, check=True), [])
        self.write("skills/uniac/references/overview.md", "Manual drift")
        (self.root / "agents/agents.md").unlink()
        self.write("skills/uniac/references/old.md", "Stale reference")
        self.write("docs/.mintlify/skills/old/SKILL.md", "Stale site skill")
        before = self.snapshot()
        self.assertEqual(set(generate(self.root, check=True)), {
            "skills/uniac/references/overview.md", "agents/agents.md",
            "skills/uniac/references/old.md", "docs/.mintlify/skills/old/SKILL.md",
        })
        self.assertEqual(before, self.snapshot())
        generate(self.root)
        self.assertEqual(generate(self.root, check=True), [])
        self.assertFalse((self.root / "skills/uniac/references/old.md").exists())
        self.assertFalse((self.root / "docs/.mintlify/skills/old/SKILL.md").exists())

    def test_unknown_pages_components_and_navigation_drift_fail_before_writing(self):
        cases = {
            "link to an unknown page: /missing": ("docs/index.mdx", '---\ntitle: "Home"\n---\n\n[x](/missing)\n'),
            "link to an unknown page: yaml.mdx": ("docs/index.mdx", '---\ntitle: "Home"\n---\n\n[x](yaml.mdx)\n'),
            "MDX components and expressions are not converted: <Note>": ("docs/index.mdx", '---\ntitle: "Home"\n---\n\n<Note>\nText\n</Note>\n'),
            "a page that becomes a skill needs a description": ("docs/quickstart.mdx", '---\ntitle: "Quickstart"\n---\n\nText\n'),
            "unlisted \\['setup'\\], missing \\['extra'\\]": ("docs/docs.json", json.dumps(
                {"navigation": {"groups": [{"group": "Uniac", "pages": ["index", "composition/yaml", "cli/overview", "quickstart", "extra"]}]}})),
        }
        for message, (name, text) in cases.items():
            with self.subTest(message=message):
                original = (self.root / name).read_text(encoding="utf-8")
                self.write(name, text)
                with self.assertRaisesRegex(ValueError, message):
                    generate(self.root)
                self.assertFalse((self.root / "skills/uniac/references").exists())
                self.write(name, original)


if __name__ == "__main__":
    unittest.main()
