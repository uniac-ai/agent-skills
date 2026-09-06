# Set up Uniac for your agent

Uniac machine setup installs the Uniac skills for the coding agent, makes
the `uniac` command available, and connects it to the user's Uniac account.
Project creation and application deployment are separate tasks.

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

Each command installs both skills globally for the named agent and answers the
installer's prompts. Repeating it updates the installed skills. Additional
integrations are listed in the installer's
[supported agents](https://github.com/vercel-labs/skills/tree/v1.5.15#supported-agents).

| Installed skill | Purpose |
|---|---|
| [uniac](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/SKILL.md) | Framework documentation: concepts, projects, services, volumes, networking, and CLI operation. |
| [uniac-quickstart](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac-quickstart/SKILL.md) | A complete first-deployment example. |

## CLI

The npm package installs the `uniac` command:

```sh
npm install -g @uniac/cli
```

## Account access

```sh
uniac auth login
```

Sign-in requires the user's browser interaction, with account creation
available there. Credential storage, renewal, and platform selection are
described in the
[authentication reference](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli/authentication.md).

## Setup state

| Command | Information available |
|---|---|
| `npx -y skills@1.5.15 list -g --json` | Installed skill names, paths, and associated agents. |
| `uniac version` | Version of the CLI available on PATH. |
| `uniac auth status` | Locally stored account sessions and expiry. |

The website has a [quickstart walkthrough](https://docs.uniac.ai/quickstart)
and a [documentation index](https://docs.uniac.ai/llms.txt) listing its pages.
