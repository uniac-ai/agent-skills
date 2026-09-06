import tempfile
import subprocess
import sys
import unittest
from pathlib import Path

from export_docs import export, pages, render


class ExportDocsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / "source"
        self.output = Path(self.directory.name) / "docs"
        self.files = {
            "agents/agents.md": "# Setup\n\nInstall the CLI.\n",
            "skills/uniac-quickstart/SKILL.md": "---\nname: uniac-quickstart\ndescription: Skill routing.\n---\n\n# Quickstart\n\nDeploy an app.\n",
            "skills/uniac/SKILL.md": "# Agent entry\n",
            "skills/uniac/references/overview.md": "# How Uniac works\n\nServices run in a project.\n",
            "skills/uniac/references/composition/yaml.md": "# Composition in YAML\n\nDescribe the application.\n",
            "skills/uniac/references/cli/overview.md": "# CLI\n\nRun commands.\n",
        }
        for name, content in self.files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def render(self, body):
        return render("# CLI\n\n" + body, "skills/uniac/references/cli/overview.md", pages(self.source), self.source)

    def test_routes_links_queries_fragments_and_unpublished_skill_entry(self):
        result = self.render(
            "[composition](../composition/yaml.md?view=all#selection) "
            "[`system`](../overview.md) [section](#commands)\n"
            "[setup](https://github.com/uniac-ai/agent-skills/blob/main/agents/agents.md#account)\n"
            "[quickstart](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac-quickstart/SKILL.md)\n"
            "[skill](../../SKILL.md) [external](https://example.com/page.md)\n"
            "[target]: ../composition/yaml.md#declarations\n"
        )
        for link in ["[composition](/composition/yaml?view=all#selection)", "[`system`](/)", "[section](#commands)",
                     "[setup](/setup#account)", "[quickstart](/quickstart)",
                     "[skill](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/SKILL.md)",
                     "[external](https://example.com/page.md)", "[target]: /composition/yaml#declarations"]:
            self.assertIn(link, result)

    def test_code_is_byte_for_byte_while_prose_is_mdx_safe(self):
        code = [
            "`[link](../missing.md) ${{api.host}} <name>`",
            "``a ` tick [link](../missing.md) {x}``",
            "```yaml\r\nvalue: '${{api.host}}'\r\nlink: '[x](missing.md)'\r\n```\r\n",
            "~~~~md\n[link](../missing.md)\n~~~\n{literal}\n~~~~\n",
        ]
        result = self.render("A <name> with {braces}.\n\n" + "\n\n".join(code))
        self.assertIn("A &lt;name> with &#123;braces&#125;.", result)
        for block in code:
            self.assertIn(block, result)

    def test_frontmatter_comes_from_heading_and_prose(self):
        export(self.source, self.output)
        quickstart = (self.output / "quickstart.mdx").read_text()
        self.assertIn('title: "Quickstart"\ndescription: "Deploy an app."', quickstart)
        self.assertNotIn("Skill routing", quickstart)
        self.assertNotIn("# Quickstart", quickstart)
        home = (self.output / "index.mdx").read_text()
        self.assertIn('title: "How Uniac works"', home)
        self.assertNotIn("sidebarTitle", home)
        self.assertFalse((self.output / "overview.mdx").exists())

    def test_metadata_uses_the_first_paragraph_starting_with_inline_code(self):
        result = self.render("`npm install -g @uniac/cli` installs the command.\n\nLater paragraph.\n")
        self.assertIn('description: "npm install -g @uniac/cli installs the command."', result)

    def test_cli_requires_a_mintlify_repository_before_touching_pages(self):
        self.output.mkdir()
        unrelated = self.output / "unrelated.mdx"
        unrelated.write_text("Keep this file")
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("export_docs.py")), "--output", str(self.output)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("containing docs.json", result.stderr)
        self.assertEqual(unrelated.read_text(), "Keep this file")

    def test_check_detects_content_missing_and_extra_pages_without_writing(self):
        export(self.source, self.output)
        self.assertEqual(export(self.source, self.output, check=True), [])
        (self.output / "composition/yaml.mdx").write_text("Manual drift")
        (self.output / "setup.mdx").unlink()
        (self.output / "obsolete.mdx").write_text("Old content")
        before = {p: p.read_bytes() for p in self.output.rglob("*.mdx")}
        self.assertEqual(set(export(self.source, self.output, check=True)), {"composition/yaml.mdx", "setup.mdx", "obsolete.mdx"})
        self.assertEqual(before, {p: p.read_bytes() for p in self.output.rglob("*.mdx")})
        export(self.source, self.output)
        self.assertEqual(export(self.source, self.output, check=True), [])
        self.assertFalse((self.output / "obsolete.mdx").exists())

    def test_broken_links_fail_before_any_page_is_written(self):
        (self.source / "skills/uniac/references/composition/yaml.md").write_text("# Composition in YAML\n\n[bad](missing.md)\n")
        with self.assertRaisesRegex(ValueError, "link target does not exist"):
            export(self.source, self.output)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
