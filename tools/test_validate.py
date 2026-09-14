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
            return validate_links([skill], root)

    def validate_skills(self, files: dict[str, str]) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            skills = root / "skills"
            for name, text in files.items():
                path = skills / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            return validate_links(sorted(skills.iterdir()), root)

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
                "[index](https://docs.uniac.ai/llms.txt) "
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

    def test_site_markdown_urls_form_one_acyclic_graph_with_the_generated_files(self):
        self.assertEqual(self.validate_skills({
            "uniac/SKILL.md": "[quickstart](https://docs.uniac.ai/quickstart.md) [cli](references/cli/overview.md)",
            "uniac-quickstart/SKILL.md": (
                "[cli](https://docs.uniac.ai/cli/overview.md#commands) "
                "[system](https://docs.uniac.ai/index.md) [setup](https://docs.uniac.ai/setup.md)"
            ),
            "uniac/references/overview.md": "# System",
            "uniac/references/cli/overview.md": "# Commands",
            "../agents/agents.md": "# Setup",
        }), [])

    def test_site_url_cycle_reports_the_closed_path(self):
        defects = self.validate_skills({
            "uniac/SKILL.md": "[quickstart](https://docs.uniac.ai/quickstart.md)",
            "uniac-quickstart/SKILL.md": "[cli](https://docs.uniac.ai/cli/overview.md)",
            "uniac/references/cli/overview.md": "[example](https://docs.uniac.ai/quickstart.md)",
        })
        self.assertEqual(defects, [
            "cyclic Markdown links: skills/uniac-quickstart/SKILL.md -> "
            "skills/uniac/references/cli/overview.md -> skills/uniac-quickstart/SKILL.md"
        ])

    def test_site_url_without_a_generated_file_fails(self):
        target = "https://docs.uniac.ai/cli/missing.md#detail"
        self.assertEqual(self.validate_skills({
            "uniac-quickstart/SKILL.md": f"[missing]({target})",
        }), [f"skills/uniac-quickstart/SKILL.md: broken link {target!r}"])

    def test_links_into_this_repository_on_github_are_rejected(self):
        target = "https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli/overview.md"
        self.assertEqual(self.validate_skills({
            "uniac-quickstart/SKILL.md": f"[cli]({target})",
            "uniac/references/cli/overview.md": "# Commands",
        }), [
            f"skills/uniac-quickstart/SKILL.md: link {target!r} reads this repository's main; "
            "link the docs.uniac.ai Markdown page"
        ])

    def test_relative_sibling_link_escapes_the_skill_directory(self):
        self.assertEqual(self.validate_skills({
            "uniac/SKILL.md": "Knowledge.",
            "uniac-quickstart/SKILL.md": "[knowledge](../uniac/SKILL.md)",
        }), [
            "skills/uniac-quickstart/SKILL.md: "
            "link '../uniac/SKILL.md' escapes the skill"
        ])

    def test_overview_composition_and_resources_allow_contextual_links_in_both_directions(self):
        self.assertEqual(self.validate_skills({
            "uniac/SKILL.md": "[system](references/overview.md) [cli](references/cli/overview.md)",
            "uniac/references/overview.md": "[yaml](composition/yaml.md) [service](resources/service.md)",
            "uniac/references/composition/yaml.md": "[system](../overview.md) [service](../resources/service.md)",
            "uniac/references/resources/service.md": "[composition](../composition/yaml.md) [volume](volume.md)",
            "uniac/references/resources/volume.md": "[service](service.md)",
            "uniac/references/cli/overview.md": "[composition](../composition/yaml.md) [service](../resources/service.md)",
        }), [])

    def test_overview_composition_and_resources_link_only_to_each_other(self):
        for layer in ("", "composition", "resources", "resources/nested"):
            parent = "../" * len(Path(layer).parts)
            targets = (
                "https://docs.uniac.ai/cli/overview.md#commands",
                parent + "cli/overview.md#commands",
                parent + "../SKILL.md",
                "https://docs.uniac.ai/quickstart.md",
                "https://docs.uniac.ai/setup.md",
            )
            for target in targets:
                with self.subTest(layer=layer, target=target):
                    source = (Path("uniac/references") / layer / "overview.md").as_posix()
                    self.assertEqual(self.validate_skills({
                        "uniac/SKILL.md": "# Uniac",
                        "uniac-quickstart/SKILL.md": "# Quickstart",
                        "uniac/references/cli/overview.md": "# CLI",
                        "../agents/agents.md": "# Setup",
                        source: f"[operation]({target})",
                    }), [
                        f"skills/{source}: Overview, Composition, and Resources link "
                        f"only to each other: {target!r}"
                    ])

    def test_explanatory_crosslinks_still_require_existing_files(self):
        self.assertEqual(self.validate_skills({
            "uniac/references/composition/yaml.md": "[service](../resources/service.md)",
        }), [
            "skills/uniac/references/composition/yaml.md: broken link '../resources/service.md'"
        ])


if __name__ == "__main__":
    unittest.main()
