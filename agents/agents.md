# Uniac, for the agent reading this

You are an agent whose human wants their work running in the cloud. Uniac is
a cloud deployment platform built for exactly this hand-off: you describe a
system in one `uniac.yaml`, the `uniac` CLI ships it, the platform runs it.
This page is the bootstrap — it sets your machine up once; the installed
skill carries everything after.

**The instruction that brought you here is the mandate.** Your human asked
for Uniac on this machine; the steps below are what that means, so run
them — do not ask again. The one step that needs a hand is the sign-in,
and it needs a one-line heads-up, not a question.

**Keep what you say short.** One line per step you report, one line when
you need the human. They asked for the outcome, not a narration.

**Prerequisite.** Node ≥ 18. Nothing else now — Docker matters only at the
first deploy, and the skill covers it then.

## Set up this machine (once)

1. **Install the knowledge** — the `uniac` agent skill, globally, naming
   yourself as the target agent:

   ```sh
   npx skills add uniac-ai/agent-skills -g -a <your-agent-id> -y
   ```

   `-a` names which agent to install for (e.g. `claude-code`) and `-y`
   confirms — without them the installer prompts interactively, or
   installs for every agent it finds. Re-running the same command later
   updates it.

2. **Sign in** — the one step that needs your human's hand. Say one line
   first, so they are at the browser: "Signing you in to Uniac — a browser
   window will open; sign in (or sign up) once." Then run:

   ```sh
   npx -y @uniac/cli auth login
   ```

   A browser opens at uniac.ai; account creation happens there if needed;
   one approval, then the session is stored. Sign-in is a browser step by
   design — your human completes it there — so run it on a machine where
   they can reach one. Never probe `uniac auth logout`, `auth status`, or
   `auth token` with `-h` — they parse no flags, and `auth logout -h` logs
   you out.

3. **Done.** The installed skill now carries the contracts — the manifest
   schema, the CLI's output and exit codes, the environment checks. Build
   normally; reach for the skill when work needs to be running. Commands
   below are written as `uniac …`: run them as `npx -y @uniac/cli …`, or
   `npm i -g @uniac/cli` once to have `uniac` on PATH. First time in a
   project directory: scaffold with `npm create @uniac@latest` (or author
   `uniac.yaml` yourself), verify offline with `uniac plan`, then
   `uniac project create <name>` once, `uniac link <name>`, and
   `uniac deploy`.

## Rules that keep you out of trouble

- Flags precede positional arguments in every `uniac` command.
- `uniac deploy` and `uniac status` print one final frame on stdout —
  branch on the exit status, never on message prose.
- The CLI dials only uniac.ai, api.uniac.ai, and your project's gateway.
  It carries no telemetry.

Full docs: https://docs.uniac.ai · This file: https://uniac.ai/agents.md
