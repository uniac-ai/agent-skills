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
npx skills add uniac-ai/agent-skills -g
```

Installs the `uniac` skill for the coding agents on the machine. Re-run the
same command to update. This is the one install line to publish — the
ecosystem leaderboard counts installs per repository slug, so every mention
should aggregate under the same one.

In Claude Code the repository is also a plugin marketplace:

```
/plugin marketplace add uniac-ai/agent-skills
/plugin install uniac@uniac
```

`/plugin marketplace update uniac` pulls later releases.

## Layout

```
skills/uniac/                 the one skill
  SKILL.md                    essential model and reference map
  references/manifest.md      uniac.yaml schema and local validation
  references/cli.md           commands, authentication, project selection,
                              output and exit codes
  references/platform.md      runtime, networking, storage and removal
agents/agents.md              the bootstrap page uniac.ai serves to agents —
                              machine setup and sign-in
tools/validate.py             frontmatter and link gate (what strict
                              installers reject, CI rejects first)
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

The installed skill provides knowledge for any Uniac task. Its root defines
the model and links to references by subject; each reference owns that
subject's detailed contract. `agents/agents.md` serves the website's machine
setup prompt. It includes an introduction to later use; the installed
references own the operational details.

## Content

Write for a capable coding agent. Keep Uniac-specific facts that change its
decisions: schema, prerequisites, effects, limits, and behavior it cannot
infer safely. Express prerequisites as conditions, not a prescribed workflow.
Use actual field names and established terms, defining Uniac concepts once.
Remove generic advice, invented labels, failure stories, and repeated facts.
Project-specific instructions belong in the customer's project; public
contracts remain in this skill rather than copied into customer `AGENTS.md`.

## Publishing

- Every claim is verified against the released `uniac` binary — prefer
  having run the command over having read about it. A wrong field is worse
  than a missing one; the skill is read by agents that cannot check it.
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
- Before pushing: `python3 tools/validate.py` and
  `python3 tools/generate_manifests.py`; CI runs both plus a live resolve
  through the ecosystem installer (`npx skills add . --list`).
