# agent-skills

The public agent knowledge for [Uniac](https://uniac.ai), a cloud deployment
platform. Everything an agent needs to build on Uniac ships from this
repository: the documentation published at [docs.uniac.ai](https://docs.uniac.ai),
the skills generated from it, and the `agents.md` bootstrap document the
website serves to visiting agents.

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

The plugin's version is the commit it was installed from, so
`/plugin marketplace update uniac` picks up every merge.

## Layout

```
docs/                         the documentation: the Mintlify project behind
                              docs.uniac.ai and the source of every file
                              generated below
  index.mdx                   system model and projects
  composition/                application description formats
  resources/                  service and volume contracts and examples
  cli/                        commands, authentication, output and errors
  setup.mdx                   machine setup: skills, CLI and account access
  quickstart.mdx              a complete first-deployment example
  docs.json                   website navigation and theme
  .mintlify/skills/           generated: the skill entries docs.uniac.ai
                              serves at /skill.md and its discovery endpoints
skills/uniac/SKILL.md         reading path and topic map
skills/uniac/references/      generated from the reference pages
skills/uniac-quickstart/      generated from the quickstart page
agents/agents.md              generated from the setup page; uniac.ai serves
                              it from a commit pinned in the website's repository
tools/generate_skills.py      every generated file above
tools/validate.py             frontmatter, links and knowledge boundaries
tools/generate_manifests.py   the plugin name, blurb, licence and links, and
                              everything rendered from them
.claude-plugin/               Claude Code marketplace + plugin manifest
.codex-plugin/plugin.json     Codex plugin manifest
plugin.json                   agent-plugins.org manifest (Cursor imports it)
LICENSE                       MIT — required by the Cursor marketplace
```

Generated files are committed because installers, Mintlify and the website
read them from this repository; CI fails when one differs from its generator's
output. Edit the pages, `skills/uniac/SKILL.md`, `docs.json` and the metadata
in `tools/generate_manifests.py`, then regenerate.

A page's title becomes the generated file's heading, its code is copied byte
for byte, and its site links become relative links inside the uniac skill and
docs.uniac.ai Markdown URLs elsewhere, so a skill installed on its own still
reaches the complete documentation. The quickstart page's description is the
`uniac-quickstart` skill's description. Pages hold no MDX components.

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

The overview and the resource pages own the platform model, capabilities,
lifecycle effects and limits. The composition and CLI pages own fields,
commands, accepted values, defaults and output, and refer to the resource
pages for platform behavior: an interface omission or default is stated as
such, never as a platform restriction. The setup and quickstart pages
demonstrate those contracts and link to their owners. The skill entry and the
website navigation route readers to the pages and hold no product facts.

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
link only to each other, while permitting contextual links within those
subjects. Cycles among entrypoints, guides and operational references remain
invalid; checks use Markdown links without a separate graph to maintain.
Pages link each other by site route (`/cli/overview`). Skill entries link
other skills' content by docs.uniac.ai Markdown URL, because skills can be
installed individually; the quickstart links to shared references rather than
back to the framework entrypoint.

Use actual field names and established terms. Remove generic advice, invented
labels, failure stories, and repetition that does not help understanding.
Project-specific instructions belong in the customer's project; public
contracts remain in this skill rather than copied into customer `AGENTS.md`.

## Publishing

- Verify command and schema contracts against the released CLI; the CLI
  reference states the release it describes. Verify platform effects at the
  deployed implementation that applies them; schema acceptance and CLI output
  do not establish runtime behavior.
- Setup verification runs the installer on the documented Node version in
  an isolated environment. Existing global binaries or agent directories
  must not supply a prerequisite or result the setup itself fails to produce.
- Keep output contracts independent of display layout. CLI documentation owns
  command arguments, flags, defaults, and parsing rules. Document actual
  release behavior in one place, including
  reserved codes and limitations, rather than a general rule followed by
  contradictory exceptions.
- `main` is the release channel: it is what `npx skills add` resolves, the
  commit the plugin manifests are versioned by, and what Mintlify publishes
  to docs.uniac.ai, so merging to it is the release. uniac.ai serves
  `agents/agents.md` from the commit pinned in the website's repository; a
  website release moves that pin.
- Publication is complete when the ordinary public URLs serve the merged
  content: the docs pages and their Markdown, `llms.txt`, `llms-full.txt`,
  `skill.md` and `uniac.ai/agents.md`. Mintlify caches `llms-full.txt` and
  `skill.md` for up to a day; report them as pending until they match.
- Before pushing: `python3 -B -m unittest discover -s tools -p 'test_*.py'`,
  `python3 tools/generate_skills.py`, `python3 tools/generate_manifests.py`,
  `python3 tools/validate.py`, and in `docs/`: `mint validate` and
  `mint broken-links` (`npm install -g mint`; mint needs Node 20.17+). CI
  runs these plus a live resolve through the ecosystem installer
  (`npx -y skills@1.5.15 add . --list`) on Node 18.
