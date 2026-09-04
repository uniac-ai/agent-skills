# Uniac, for the agent reading this

**Your human asked for Uniac on this machine. Run the steps below without
asking again, and keep what you say to one line per step.** The one step
that needs their hand is the sign-in; give it a one-line heads-up, not a
question.

Uniac is a cloud deployment platform: you describe a system in one
`uniac.yaml`, the `uniac` CLI ships it, the platform runs it. This page sets
your machine up once; the installed skill carries everything after.

**Prerequisite:** Node ≥ 18. Docker matters only at the first deploy, and
the skill covers it then.

## 1. Install the knowledge

```sh
npx skills add uniac-ai/agent-skills -g -a <your-agent-id> -y
```

- `-a <your-agent-id>` is the agent this install is for (`claude-code`,
  `codex`, `cursor`, …); `-g` installs for the machine; `-y` answers the
  installer's prompts. Without `-a` and `-y` the installer prompts, or
  installs for every agent it finds.
- Re-running the same command later updates the skill.

## 2. Sign in

Say this first, so your human is at the browser:

```text
Signing you in to Uniac — a browser window will open; sign in (or sign up) once.
```

Then run:

```sh
npx -y @uniac/cli auth login
```

- A browser opens at uniac.ai; account creation happens there if needed;
  one approval, then the session is stored.
- Your human completes sign-in in the browser, so run it on a machine
  where they can reach one.
- The stored session lasts three days; then the same sign-in repeats.

## 3. Done

- The installed skill carries everything else: what a project, a
  deployment and a link are; how to verify a manifest offline, deploy,
  observe and remove; the `uniac.yaml` schema; the CLI's output and exit
  codes. Read it before the first Uniac work in a project.
- Commands in the skill and docs are written as `uniac …`: run them as
  `npx -y @uniac/cli …`, or `npm i -g @uniac/cli` once to have `uniac` on
  PATH.

## Rules

- Flags precede positional arguments in every `uniac` command.
- `uniac deploy` and `uniac status` print one final frame on stdout;
  branch on the exit status, never on message prose.
- The CLI dials only uniac.ai, api.uniac.ai, and your project's gateway,
  and carries no telemetry.

Full docs: https://docs.uniac.ai · This file: https://uniac.ai/agents.md
