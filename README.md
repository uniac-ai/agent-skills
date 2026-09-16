# agent-skills

The public agent knowledge for [Uniac](https://uniac.ai), a cloud deployment
platform: one skill, `uniac`, that gives a coding agent an expert's working
knowledge of building and operating applications on Uniac. The documentation
at [docs.uniac.ai](https://docs.uniac.ai) is the source of every contract;
the skill compresses it and names the page for each detail.

The audience is a **consumer of Uniac** — an agent (or the engineer directing
it) with an application that needs to be running. Nothing here assumes access
to Uniac's own source, and nothing here documents how the platform is built.

## Install

```sh
npx -y skills@1.5.15 add uniac-ai/agent-skills -g
```

Offers the skill to the coding agents on the machine; re-run to update. The
installer is pinned for Node 18 compatibility.

In Claude Code the repository is also a plugin marketplace:

```
/plugin marketplace add uniac-ai/agent-skills
/plugin install uniac@uniac
```

The plugin's version is the commit it was installed from, so
`/plugin marketplace update uniac` picks up every merge.

## Layout

```
skills/uniac/SKILL.md          the model, the workflow, the decisions, what goes wrong
skills/uniac/references/
  composition.md               uniac.yaml: fields, names, references, a complete example
  platform.md                  services, replicas, networking, environment, volumes, limits
  operations.md                the CLI: commands, destinations, credentials, output, exit codes
tools/validate.py              frontmatter, links and docs URLs
.claude-plugin/                Claude Code marketplace + plugin manifest
.codex-plugin/plugin.json      Codex plugin manifest
plugin.json                    agent-plugins.org manifest (Cursor imports it)
LICENSE                        MIT — required by the Cursor marketplace
```

## Writing

The skill is a compression, not a copy. `SKILL.md` is what an expert keeps in
their head: the model, the working order, the decisions and their reasons,
and the ways things go wrong. The references hold the compact facts an agent
needs while writing a composition or reading the CLI, each pointing at the
documentation page that owns the complete contract
(`https://docs.uniac.ai/<page>.md`).

- State judgment and procedure here; state contracts once, in the docs. A
  number, field or limit repeated here is repeated only because an agent
  needs it in hand while writing, and it names the owning page beside it.
- Describe the current release of the CLI and the platform as they are;
  when either changes, this skill changes in the same review cycle.
- Keep `SKILL.md` under 500 lines and references one link away from it.
  Assume a capable agent: no generic advice, no explanations of Docker, YAML
  or containers.
- Links to other pages use `https://docs.uniac.ai/<page>.md` (the Markdown
  the site serves), never a repository URL.

## Checks

`python3 tools/validate.py` checks every skill's frontmatter against the
strictest installers, that relative links resolve inside the skill, that no
site-route link (`/page`) remains, and that every `docs.uniac.ai` Markdown
URL answers. CI runs it and a live resolve through the ecosystem installer
on every pull request and push to `main`. Merging to `main` is the release:
it is what `npx skills add` and the plugin marketplace fetch.
