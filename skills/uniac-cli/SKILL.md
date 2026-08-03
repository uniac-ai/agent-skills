---
name: uniac-cli
description: Drive the uniac CLI programmatically — the command surface (init, plan, link, deploy, status, auth, version), the final text frame deploy and status leave on stdout, the typed error codes and exit statuses, and the headless environment variables. Load before running, scripting, or parsing the output of any uniac command.
---

# The `uniac` CLI as an operational surface

The CLI reports state, not narration. Two commands — `deploy` and `status` —
are **state gateways**: each leaves exactly one plain-text **final frame** on
stdout and says nothing else there. Everything you need to decide what to do
next is in that frame and the exit status.

Install: `npm i -g @uniac/cli`. Check the build with `uniac version`.

## Commands

| Command | Network | Docker | What it does |
|---|---|---|---|
| `uniac init` | no | no | Interactive scaffold of `uniac.yaml`: one service plus the deployment instantiating it. Refuses to overwrite an existing manifest. |
| `uniac plan [resource]` | no | no | Resolve the target and preview the deployable. The offline verification loop. |
| `uniac link [name\|slug]` | yes | no | Bind this directory to a remote project; writes `.uniac/deploy.json`. |
| `uniac deploy [resource]` | yes | **yes** | Resolve, materialize, push, register, then watch the platform until the deployment settles. |
| `uniac status [service]` | yes | no | Report what the linked project is running. Changes nothing. |
| `uniac auth login\|status\|token\|logout` | login only | no | Manage the stored session (`~/.uniac/auth.json`). |
| `uniac version` | no | no | Build metadata. |

`deploy` needs a running Docker daemon: it pulls the declared image locally
using **your own** docker credentials (`config.json` and its helpers, exactly
like `docker pull`), then pushes to the project registry. A private base image
that your local docker cannot pull will fail the build phase.

Both `plan` and `deploy` target a **deployment**: the named resource, else the
manifest's `default`, else its only deployment.

`deploy` blocks while the platform's deployment task runs, polling every 2s for
up to 5 minutes, and reports what the service settled as — registration alone
is not success. Interrupting it does not cancel the platform-side work; run
`uniac status` to see where it landed.

**Flags precede the positional argument.** Parsing stops at the first non-flag
token, so `uniac plan database --json` silently ignores `--json`;
`uniac plan --json database` honors it. `plan`, `deploy`, and `status` locate
the project with `--dir`; `link` uses `-C`.

## The output contract

This section is the contract of the two state-gateway commands, `deploy` and
`status`.

**Their stdout carries exactly one final frame per run — nothing else, ever.**
There is no machine encoding to select: no `-o`/`--output` flag and no
`UNIAC_OUTPUT` variable exist, and passing `-o json` is a usage error. The text
frame is the output. The only JSON surface is `uniac plan --json` — the
deployable artifact, a different mechanism.

A terminal is never consulted for the frame: the same run piped, captured, or
under a pty leaves identical bytes on stdout whatever the watch mode, and a
human's terminal is left holding exactly the text an agent captures.

### The final frame

A run is a tree of tasks, and a subtask's output stops mattering the moment it
completes. The frame is what remains:

- **Success** — the root line, then the state block. Completed work folds to
  nothing; the state is the story.
- **Failure** — the spine of the failure path: each node on the path lists its
  completed subtasks as one-liners and expands the failing one down to its
  retained evidence lines, then the state block with a typed `error`.

A real failure frame (exit 6; evidence lines are verbatim tool output):

```
✗ deploy d  (2.1s)
  ✓ plan  sha256:01ecf3fff875
  ✓ link  test-x
  ✗ build  (2.1s)
      ✗ pull ghcr.io/uniac-ai/does-not-exist:1.0  (2.1s)
      image-pull[…]: pull ghcr.io/uniac-ai/does-not-exist:1.0: Error response from daemon: error from registry: denied
      denied

project  test-x

service  hello
  image  ghcr.io/uniac-ai/does-not-exist:1.0

error      build
  message  image-pull[…]: pull ghcr.io/uniac-ai/does-not-exist:1.0: Error response from daemon: error from registry: denied
```

### The state block

The frame ends with the state block: `key  value` rows aligned by two-space
columns, sub-rows indented two spaces, sections separated by blank lines. **An
omitted row is an absent fact, never a hidden one** — the account states only
what the run actually established.

```
project  <slug>

service  <name>  v<version>
  image  <source ref the manifest declared>
  digest  <registry manifest digest this run published>
  status  <status> (<observed>/<effective>)
  kind  stateful
  endpoint  <address> → :<port>
  hold  <reason>
  warning  <condition>

error      <code>
  message  <prose>
  retryable  yes
```

- One `service` section per service. A project is a flat list of services; the
  manifest's deployment is a client-side composition and never appears.
- `v<version>` numbers the serving deployment — "which state is this service
  in". Present only once the platform has one.
- `image` is known only to a run that read the manifest; `digest` only to a
  run that published one.
- `status` is the platform's word for what the service is doing; the
  `(observed/effective)` replica count appears when the platform reported one.
- `kind stateful` marks a service the platform runs as exactly one instance;
  the row is absent for a stateless service.
- `endpoint`: the address is the whole string to dial — `https://<hostname>`
  for `http` claims, `<host>:<allocated-port>` for `tcp`. The trailing
  `→ :<port>` is the service's own listen port that traffic lands on, which
  appears nowhere in the address.
- `hold` rows are platform-side reasons the service is not converging;
  `warning` rows are conditions the run succeeded despite — a dangling
  `${{...}}` reference shows up here.
- `error` appears when the run failed: the code from the closed set below,
  the message (prose for people — never match on it), and `retryable  yes`
  when the platform judges the identical command could succeed re-run as-is.

**A failed run still leaves its frame** — whatever state it did establish,
then the `error`. A failed deploy still lists the services it was working on.
Never treat a non-zero exit as "no output".

### Watching a run

Live rendering is a stderr concern and never changes a byte of stdout. The
mode, first match wins:

1. `UNIAC_PROGRESS=0` — silent. `UNIAC_PROGRESS=1` — plain progress lines
   streamed to stderr as they happen (the CI-log form).
2. An agent harness variable set (`CLAUDECODE`, `AI_AGENT`, `AGENT`,
   `CODEX_SANDBOX`, `CURSOR_AGENT`, `GEMINI_CLI`) — silent, even under a pty.
3. Both stdout and stderr are terminals — a live task tree repaints on stderr
   and is erased when the run ends.
4. Otherwise silent: nothing until the final frame.

Rendering starts only once linking can no longer prompt, so a run that fails
at the plan or link step emits nothing to stderr even with `UNIAC_PROGRESS=1`.

## Exit statuses and error codes

Each code maps to exactly one status, and the frame's `error` row carries the
code. **1 is deliberately unassigned** by the state-gateway commands, so a bare
`exit 1` from some future dependency can never be mistaken for a meaning the
CLI assigned.

| Exit | `error` code | Meaning | What to do |
|---|---|---|---|
| 0 | — | Success. | Read the state block. |
| 2 | `usage` | Malformed invocation. Nothing was sent anywhere. | Fix the arguments. |
| 3 | `auth` | Missing or rejected credential. | `uniac auth login`, or set `UNIAC_ACCESS_TOKEN`. |
| 4 | `not_linked` | Directory not bound to a remote project. | `uniac link`, or set `UNIAC_PROJECT_URL`. |
| 5 | `manifest` | `uniac.yaml` does not describe a valid system. | Fix the manifest; `uniac plan` reproduces it offline. |
| 6 | `build` | Failed obtaining or materializing a container. | Check the image reference and the Docker daemon. |
| 7 | `push` | Failed publishing the image to the registry. | Usually retryable. |
| 8 | `deploy_failed` | The platform's deployment task failed. | Terminal unless `retryable` says otherwise. |
| 9 | `unreachable` | The platform did not answer; nothing was decided either way. | Retry with backoff. |
| 10 | `pending` | **Not a failure** — the work is still running. | Re-observe with `uniac status`. |
| 70 | `internal` | A defect in the CLI. | Report it with the message. |

Rules for consuming this:

- **Branch on the exit status; read the `error` row for detail.** Never match
  on the message — prose is for people, and rewording it would silently change
  your behavior.
- **Never treat exit 10 as failure.** A consumer that does will abandon
  deployments that are about to succeed.
- **Treat any unrecognized code as internal.** The set is closed and additions
  are additive; surface the message rather than guessing.
- `retryable` is the platform's own judgment on whether re-running the
  identical command could succeed with nothing else changed. Prefer it to your
  own heuristics.
- **Read the message on exit 70 before calling it a CLI defect.** As of
  v0.3.8, exits 4 and 10 are reserved but nothing produces them: `deploy`
  watches its deployment task to settlement (a deadline expiry arrives as exit
  8, `still <state> after 5m0s — check the dashboard`), and an unlinked
  directory arrives as exit 3 when no credential is stored or as exit 70 with
  the accurate message `project not linked. Run \`uniac link\` or set
  UNIAC_PROJECT_URL` when one is.

`plan`, `init`, `link`, and `auth` are **not** state-gateway commands: they are
human-oriented, print to stdout in their own shapes, and exit `1` on error, `2`
on a usage error. `uniac plan --json` emits `{resource, digest, deployable}` —
useful and stable.

## Headless operation

| Variable | Effect |
|---|---|
| `UNIAC_ACCESS_TOKEN` | Bypasses interactive login. |
| `UNIAC_PROJECT_URL` | Targets a project by full URL or bare slug, bypassing `.uniac/deploy.json` and the interactive picker. `deploy` only — see below. |
| `UNIAC_PROGRESS` | `1` forces stderr progress lines, `0` silences them. Never affects stdout. |
| `UNIAC_STORE_DIR` | Local artifact store location (default `~/.uniac/store`). |
| `UNIAC_AUTH_HOST` | The host serving the `/cli/auth` handoff (default `uniac.ai`). |

`UNIAC_ACCESS_TOKEN` + `UNIAC_PROJECT_URL` together are the fully headless
**deploy** path: no picker, no browser. Without a link binding and without the
override, `uniac deploy` drops into the interactive project picker — which will
hang a non-interactive caller, so always set one of them in CI.

**`uniac status` cannot use the override.** An override names a target but not
a project, and `status` reads by project name — under `UNIAC_PROJECT_URL` it
fails with exit 3 and the misleading message `this directory is not linked to a
project` even in a linked directory, because the override wins over the
binding. Observation needs the real link binding: run `uniac link` once, and
unset `UNIAC_PROJECT_URL` when running `status`.

`.uniac/deploy.json` holds `{project_slug, project_name, gateway_url}` and is
per-checkout environment state, not source. Gitignore it.

## The loop an agent should run

```sh
uniac plan --json     # offline; fix the manifest until this passes
uniac deploy; echo $? # branch on the status, read the frame's state block
uniac status          # re-observe at any time; changes nothing
```

`deploy` and `status` project the same facts through the same code, so what a
deploy reports and what an observation reports cannot drift into two accounts
of one system. When a deploy's account looks stale or incomplete, `uniac
status` is the authoritative re-read.
