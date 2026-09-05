# Set up Uniac for your agent

Uniac machine setup makes the `uniac` skill available to the coding agent
and connects the CLI to the user's Uniac account. Project creation and
application deployment are separate tasks.

The setup commands require Node 18+.

## Agent knowledge

### Claude Code

```sh
npx -y skills@1.5.15 add uniac-ai/agent-skills -g -a claude-code -y
```

### Codex

```sh
npx -y skills@1.5.15 add uniac-ai/agent-skills -g -a codex -y
```

### Cursor

```sh
npx -y skills@1.5.15 add uniac-ai/agent-skills -g -a cursor -y
```

Each command installs `uniac` globally for the named agent and answers the
installer's prompts. Repeating it updates the installed skill. Additional
integrations are listed in the installer's
[supported agents](https://github.com/vercel-labs/skills/tree/v1.5.15#supported-agents).

The installed [Uniac skill](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/SKILL.md)
is the entrypoint for the platform's system model, manifest, and operations.

## Account access

The CLI can run through `npx` without a global installation:

```sh
npx -y @uniac/cli auth login
```

Sign-in requires the user's browser interaction, with account creation
available there. The CLI stores the resulting session. Credential storage,
expiry, and platform selection are described in the
[CLI reference](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli.md#authentication).

## Setup state

| Command | Information available |
|---|---|
| `npx -y skills@1.5.15 list -g --json` | Installed skill names, paths, and associated agents. |
| `npx -y @uniac/cli auth status` | Stored account sessions and expiry, without server validation. |

[Full documentation](https://docs.uniac.ai).
