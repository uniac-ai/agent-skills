# agent-skills

The public agent knowledge for [Uniac](https://uniac.ai), a cloud deployment
platform. Everything an agent needs to build on Uniac ships from this
repository: the `uniac` skill (with its bundled contract references), and the
`agents.md` bootstrap document the website serves to visiting agents.

The audience is a **consumer of Uniac** — an agent (or the engineer directing
it) with an application that needs to be running. Nothing here assumes access
to Uniac's own source, and nothing here documents how the platform is built.

## Install

```sh
npx -y skills@1.5.15 add uniac-ai/agent-skills -g
```

Installs the `uniac` skill for the coding agents on the machine. Re-run the
same command to update. Installation examples use `uniac-ai/agent-skills`;
the ecosystem leaderboard counts installs per repository slug.

The installer is pinned for Node 18 compatibility; it fetches this repository's
current skill. CI checks installer discovery on Node 18.

In Claude Code the repository is also a plugin marketplace:

```
/plugin marketplace add uniac-ai/agent-skills
/plugin install uniac@uniac
```

`/plugin marketplace update uniac` pulls later releases.

## Layout

```
skills/uniac/                 the one skill
  SKILL.md                    platform goal, system composition, reference map
  references/manifest.md      uniac.yaml schema and local validation
  references/cli.md           commands, authentication, project selection,
                              output and exit codes
  references/platform.md      runtime, networking, storage and removal
agents/agents.md              machine setup: agent knowledge and account access
tools/validate.py             frontmatter, links, and reference-cycle checks
tools/generate_manifests.py   the plugin name, release, blurb, licence and
                              links, and everything rendered from them
.claude-plugin/               Claude Code marketplace + plugin manifest
.codex-plugin/plugin.json     Codex plugin manifest
plugin.json                   agent-plugins.org manifest (Cursor imports it)
.well-known/agent-skills/     the discovery index and the skill archive
                              it points at
LICENSE                       MIT — required by the Cursor marketplace
```

Plugin manifests, the discovery index, and the skill archive are generated.
`tools/generate_manifests.py` holds their shared metadata; CI runs it with
`--check` to verify that the committed files match their sources.

The installed skill separates the platform's goal, system composition,
static declaration, and live operation. `agents/agents.md` defines the
website's machine setup outcome and provides installation, account access,
and commands for inspecting setup state. The installed references own the detailed
authentication and operational contracts.

## Content

Write for a capable coding agent. Keep Uniac-specific facts: schema,
prerequisites, effects, limits, and behavior. Review document boundaries,
sections, and paragraphs before individual sentences. Each passage should
explain one concern coherently, with the context needed to understand it.
Judge each document against the outcome promised where readers enter it.
Then check its sentences, tables, and examples for directives and information
derivable from retained facts. Remove repeated explanations and constructed
procedures while preserving their independently useful premises.

Describe what commands, files, and the platform do. A directive is justified
only by an essential user-experience requirement that the agent cannot infer
from those facts. State its concrete reason. First check whether the missing
knowledge is a prerequisite or side effect, and document that instead.
Permission, communication, and execution policies belong to the agent's
managing layer. Product confirmation controls are facts about the interface.

Organize knowledge from the platform's goal to its components and their
relationships, then the manifest that declares them, then CLI and platform
operation. This order expresses levels of explanation, not steps to execute.
The entrypoint explains the goal and core system model; references own
substantial, distinct subjects. Layers organize concepts without requiring
a file per layer. Keep syntax, tooling, and runtime mechanisms below the
system model, and keep field semantics together with their declarations.
Links lead to more detailed contracts; shared detail has one owner, and
references must not form cycles. CI checks cycles from the Markdown links
themselves, without a separate graph to maintain.

Use actual field names and established terms, defining Uniac concepts once.
Remove generic advice, invented labels, failure stories, and repeated facts.
Project-specific instructions belong in the customer's project; public
contracts remain in this skill rather than copied into customer `AGENTS.md`.

## Publishing

- Every claim is verified against the released `uniac` binary — prefer
  having run the command over having read about it. A wrong field is worse
  than a missing one; the skill is read by agents that cannot check it.
- Setup verification runs the installer on the documented Node version in
  an isolated environment. Existing global binaries or agent directories
  must not supply a prerequisite or result the setup itself fails to produce.
- Keep output contracts independent of display layout. Command help owns
  the flag inventory; the reference retains parsing hazards that make
  discovery unsafe. Document actual release behavior in one place, including
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
- Before pushing: `python3 -B tools/test_validate.py`, `python3 tools/validate.py`, and
  `python3 tools/generate_manifests.py`; CI runs these plus a live resolve
  through the ecosystem installer (`npx -y skills@1.5.15 add . --list`).
