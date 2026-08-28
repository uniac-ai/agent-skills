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
same command to update. Once the discovery index is served, the domain form
works too: `npx skills add uniac.ai`.

## Layout

```
skills/uniac/                 the one skill
  SKILL.md                    resident knowledge: mental model, loop,
                              commands, environment, sharp edges
  references/manifest.md      full uniac.yaml schema, reference grammar,
                              plan-time rules, multi-service composition
  references/cli.md           the final-frame output contract, state-block
                              rows, typed exit codes, headless env vars
agents/agents.md              the bootstrap page uniac.ai serves to agents —
                              machine setup and sign-in, before knowledge
                              is installed
tools/validate.py             frontmatter and link gate (what strict
                              installers reject, CI rejects first)
tools/generate_index.py       emits .well-known/agent-skills/index.json
                              (per-file sha256 digests) for the website
.well-known/agent-skills/     the committed discovery index
```

One skill by design: an agent's Uniac task always needs the mental model,
the manifest, and the CLI together, so they load as one body with the deep
contracts as on-demand references. A second skill appears only when a
distinct activity earns it.

The boundary with `agents/agents.md`: the bootstrap document carries only
what an agent needs *before* the skill is installed (consent etiquette,
the install line, sign-in); the skill carries everything after. Neither
restates the other.

## Publishing

- Every claim is verified against the released `uniac` binary — prefer
  having run the command over having read about it. A wrong field is worse
  than a missing one; the skill is read by agents that cannot check it.
- Current verification stamp: **v0.3.12**.
- At each CLI release the contracts are re-verified against, tag this
  repository `v<cli-version>`. The UniacWeb build vendors the tag matching
  the released CLI and serves `agents.md`, the skill files, and the
  discovery index same-origin at uniac.ai.
- Before pushing: `python3 tools/validate.py` and
  `python3 tools/generate_index.py`; CI runs both plus a live resolve
  through the ecosystem installer (`npx skills add . --list`).
