# agent-skills

The public agent knowledge for [Uniac](https://uniac.ai), a cloud deployment
platform. Everything an agent needs to build on Uniac ships from this
repository: framework knowledge, a first-deployment quickstart, and the
`agents.md` bootstrap document the website serves to visiting agents.

The audience is a **consumer of Uniac** — an agent (or the engineer directing
it) with an application that needs to be running. Nothing here assumes access
to Uniac's own source, and nothing here documents how the platform is built.

## Install

```sh
npx -y skills@1.5.15 add uniac-ai/agent-skills -g
```

Offers the Uniac skills for the coding agents on the machine. Re-run the
same command to update. Installation examples use `uniac-ai/agent-skills`;
the ecosystem leaderboard counts installs per repository slug.

The installer is pinned for Node 18 compatibility; it fetches this repository's
current skills. CI checks installer discovery on Node 18.

In Claude Code the repository is also a plugin marketplace:

```
/plugin marketplace add uniac-ai/agent-skills
/plugin install uniac@uniac
```

`/plugin marketplace update uniac` pulls later releases.

## Layout

```
skills/uniac/                 framework documentation
  SKILL.md                    reading path and topic map
  references/overview.md      system model and projects
  references/composition/     application description formats
  references/resources/       service and volume contracts and examples
  references/cli/             commands, authentication, output and errors
skills/uniac-quickstart/       a complete first-deployment example
agents/agents.md              machine setup: skills, CLI and account access
tools/validate.py             frontmatter, links and knowledge boundaries
tools/export_docs.py          website pages generated from these sources
tools/generate_manifests.py   the plugin name, release, blurb, licence and
                              links, and everything rendered from them
.claude-plugin/               Claude Code marketplace + plugin manifest
.codex-plugin/plugin.json     Codex plugin manifest
plugin.json                   agent-plugins.org manifest (Cursor imports it)
LICENSE                       MIT — required by the Cursor marketplace
```

Plugin manifests are generated from shared metadata in
`tools/generate_manifests.py`; CI checks that committed files match.
Installers load the skill source directories. Distribution artifacts need
a supported consumer and a verified installation path.

The references, setup document, and quickstart are the authored documentation.
`tools/export_docs.py` generates their website pages with the same content,
adapting frontmatter and links for Mintlify. UniacDocs records the source
commit and checks the generated pages against it. Website navigation and
`SKILL.md` expose the same subjects; neither maintains a second explanation.

## Content

Write for a capable coding agent. Keep Uniac-specific facts: schema,
prerequisites, effects, limits, and behavior. Review document boundaries,
sections, and paragraphs before individual sentences. Each passage should
explain one concern coherently, with the context needed to understand it.
Judge each document against the outcome promised where readers enter it.
Then check its sentences, tables, and examples for directives and information
derivable from retained facts. Remove repeated explanations and constructed
procedures while preserving their independently useful premises. Operations
state their required inputs and effects, referencing the concepts that own
those inputs. A quickstart illustrates these contracts; missing prerequisites
or relationships are repaired in their owning reference. Its example order
applies to its stated starting conditions, not to every task.

Describe what commands, files, and the platform do. A directive is justified
only by an essential user-experience requirement that the agent cannot infer
from those facts. State its concrete reason. First check whether the missing
knowledge is a prerequisite or side effect, and document that instead.
Permission, communication, and execution policies belong to the agent's
managing layer. Product confirmation controls are facts about the interface.

The entrypoint gives a short reading path through the top-level system
overview, composition, and CLI before offering detailed references.
Composition contains application description formats. The introduction
explains how the parts work together, including what runs and how reusable
definitions become running instances; a glossary or topic catalog does not
establish those relationships. The path teaches the system,
not an assumed command sequence. The overview, Composition, and Resources
describe the system independently of the CLI. Resource pages distinguish
required and optional configuration from examples in a composition language.
Keep topics normally needed together in one document with sections; separate
references serve independently useful questions.
Brief restatement and cross-links between composition and resource examples
are useful when they let each page be understood in context; full contracts
still have one owner. Progressive disclosure controls loading, not which
knowledge is available, and the website publishes these same sources.
Authentication owns credential acquisition, renewal, selection, and status
semantics; commands that use credentials inherit that contract. Conditional
requirements stay with the operation that needs them, rather than becoming
default setup steps. CI checks that the overview, Composition, and Resources
do not link to CLI or skill entrypoints, while permitting contextual links
within those subjects. Cycles among entrypoints, guides and operational references remain
invalid; checks use Markdown links without a separate graph to maintain.
Cross-skill references use canonical HTTPS URLs because skills can be
installed individually. Quickstart links to shared references rather than
back to the framework entrypoint.

Use actual field names and established terms. Remove generic advice, invented
labels, failure stories, and repetition that does not help understanding.
Project-specific instructions belong in the customer's project; public
contracts remain in this skill rather than copied into customer `AGENTS.md`.

## Publishing

- Verify command and schema contracts against the released CLI. Verify
  platform effects at the deployed implementation that applies them;
  schema acceptance and CLI output do not establish runtime behavior.
- Setup verification runs the installer on the documented Node version in
  an isolated environment. Existing global binaries or agent directories
  must not supply a prerequisite or result the setup itself fails to produce.
- Keep output contracts independent of display layout. CLI documentation owns
  command arguments, flags, defaults, and parsing rules. Document actual
  release behavior in one place, including
  reserved codes and limitations, rather than a general rule followed by
  contradictory exceptions.
- The verification stamp is `VERSION` in `tools/generate_manifests.py`. It is
  the release the contracts were checked against, and the version every
  plugin manifest carries.
- At each CLI release the contracts are re-verified against, bump that
  constant, regenerate, and tag this repository `v<cli-version>`. Tags are
  provenance and rollback; nothing installs from them. `main` is the release
  channel — it is what `npx skills add` resolves, and what uniac.ai takes
  `agents.md` from, so merging to it is the release.
- Before pushing: `python3 -B -m unittest discover -s tools -p 'test_*.py'`, `python3 tools/validate.py`, and
  `python3 tools/generate_manifests.py`; CI runs these plus a live resolve
  through the ecosystem installer (`npx -y skills@1.5.15 add . --list`).
