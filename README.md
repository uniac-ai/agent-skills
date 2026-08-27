# UniacAppSkill

Agent skills for building and operating an application on [Uniac](https://uniac.ai), a cloud deployment platform.

The audience is a **consumer of Uniac** — an agent (or the engineer directing it) with an application that needs to be running. Nothing here assumes access to Uniac's own source, and nothing here documents how the platform is built.

| Skill | Covers |
|---|---|
| `uniac-app` | Entry point. What Uniac is, the mental model (services are reusable definitions; deployments instantiate them), the project loop, what the platform owns. Load on any Uniac signal. |
| `uniac-manifest` | The full `uniac.yaml` schema: resources, `type: service`, `type: stateful`, `type: deployment`, the `image:` / `build:` source choice, `volumes:` durable storage on a stateful service, `public_ports` and their tri-state semantics, the `${{service.VAR}}` reference grammar, and every rule that fails at plan time. |
| `uniac-cli` | The CLI as an operational surface: the command set, the plain-text frame `deploy` leaves on stdout and the state block `status` leaves there, typed error codes and exit statuses, headless environment variables. |
| `uniac-multi-service` | Composing several services into one system: cross-service wiring, public exposure, deploy ordering, and what the platform does not provide. |

Uniac's CLI is designed agent-first: `deploy` and `status` answer on stdout with a plain-text frame rather than narration, behind typed error codes and exit statuses, and `uniac plan` verifies a manifest offline, without credentials. These skills are written to that surface; `uniac-cli` specifies it in full.

Every claim was verified against the `uniac` CLI at v0.3.12 and its shipped contracts, not from memory.

## Install

```bash
bash install.sh
```

Per skill `<name>`, creates:

```
~/.agents/skills/<name>  ->  <this checkout>/skills/<name>   # global entry
~/.claude/skills/<name>  ->  ../../.agents/skills/<name>     # Claude Code
~/.codex/skills/<name>   ->  ../../.agents/skills/<name>     # Codex
```

Every agent consumes the same copy, and that copy is this checkout — content edits are live through the links. Idempotent; re-run only when a skill is added or renamed. Skips (with a warning) any destination that already exists and is not a symlink.

Skill names are a global namespace shared by every installed skill repo, so a same-named skill from elsewhere would be relinked here.

## Add a skill

```bash
mkdir skills/<name>
$EDITOR skills/<name>/SKILL.md
bash install.sh
```

`SKILL.md` needs at minimum a YAML frontmatter block with `name` and `description`. The description is what an agent reads to decide whether to load the skill, so it should name the triggering situation, not just the topic.

## Remove a skill

```bash
rm -rf skills/<name>
rm ~/.agents/skills/<name> ~/.claude/skills/<name> ~/.codex/skills/<name>
```

## Layout

```
.
├── install.sh         # idempotent symlinker (global entry + per-agent links)
├── skills/
│   └── <name>/        # one directory per skill
│       └── SKILL.md
└── README.md
```

## Contributing

A skill is read by agents that cannot check it, so a wrong field is worse than a missing one. Verify against the shipped CLI — prefer having run the command over having read about it — and prefer stating durable contracts (the manifest schema, the output document, the exit codes) over enumerating surfaces likely to churn while Uniac is pre-1.0.
