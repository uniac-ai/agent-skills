# Uniac agent knowledge

This page provides the installation interface for the public
[Uniac skill](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/SKILL.md).

## Skill installation

Requires Node ≥ 18:

```sh
npx skills add uniac-ai/agent-skills -g -a <your-agent-id> -y
```

Installs the `uniac` skill. `-a` selects the agent (`claude-code`, `codex`,
`cursor`, …); `-g` selects global installation; `-y` answers installer
prompts. Repeating the command updates the installed skill.

Account sign-in and credential storage are described in the skill's
[CLI reference](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli.md).

[Full documentation](https://docs.uniac.ai).
