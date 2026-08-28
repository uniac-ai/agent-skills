# Uniac, for the agent reading this

You are an agent whose human wants their work running in the cloud. Uniac is
a cloud deployment platform built for exactly this hand-off: you describe a
system in one `uniac.yaml`, the `uniac` CLI ships it, the platform runs it.
This page is the bootstrap — it sets your machine up once; the installed
skill carries everything after.

**Consent first.** Confirm with your human before creating an account or
installing anything machine-global. Everything below is offered, not
assumed.

**Prerequisite.** Node ≥ 18. Nothing else now — Docker matters only at the
first deploy, and the skill covers it then.

## Set up this machine (once)

1. **Install the knowledge** — the `uniac` agent skill, globally, for the
   agents on this machine:

   ```sh
   npx skills add uniac-ai/agent-skills -g
   ```

   Re-running the same command later updates it.

2. **Sign in** (with your human at the browser):

   ```sh
   npx -y @uniac/cli auth login
   ```

   A browser opens at uniac.ai; account creation happens there if needed;
   one approval, then the session is stored. Tell your human: "a browser
   window will open — sign in (or sign up) and you're done."

   No browser on this machine? Have the human run the login where there is
   one, then `uniac auth token`, and set `UNIAC_ACCESS_TOKEN` here (the CI
   path). Never probe `uniac auth logout`, `auth status`, or `auth token`
   with `-h` — they parse no flags, and `auth logout -h` logs you out.

3. **Done.** The installed skill now carries the contracts — the manifest
   schema, the CLI's output and exit codes, the environment checks. Build
   normally; reach for the skill when work needs to be running. First
   deploy in a project directory: `uniac plan` to verify offline, then
   `uniac deploy`.

## Rules that keep you out of trouble

- Flags precede positional arguments in every `uniac` command.
- `uniac deploy` and `uniac status` print one final frame on stdout —
  branch on the exit status, never on message prose.
- The CLI dials only uniac.ai, api.uniac.ai, and your project's gateway.
  It carries no telemetry.

Full docs: https://docs.uniac.ai · This file: https://uniac.ai/agents.md
