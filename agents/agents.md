# Set up Uniac for your agent

Uniac machine setup makes the `uniac` skill available to the coding agent
and connects the CLI to the user's Uniac account. Project creation and
application deployment are separate tasks.

## Agent knowledge

The skill installer requires Node ≥ 22.20.0:

```sh
npx skills add uniac-ai/agent-skills -g -a <your-agent-id> -y
```

Installs the `uniac` skill. `-a` selects the agent (`claude-code`, `codex`,
`cursor`, …); `-g` selects global installation; `-y` answers installer
prompts. Repeating the command updates the installed skill.

The installed [Uniac skill](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/SKILL.md)
is the entrypoint for the platform's system model, manifest, and operations.

## Account access

The CLI requires Node ≥ 18 and can run through `npx` without a global installation:

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
| `npx skills list -g --json` | Installed skill names, paths, and associated agents. |
| `npx -y @uniac/cli auth status` | Stored account sessions and expiry, without server validation. |

[Full documentation](https://docs.uniac.ai).
