---
name: uniac-cli
description: Drive the uniac CLI programmatically — the command surface (init, plan, link, deploy, status, auth, version), the uniac/v1 state document on stdout, the typed error codes and exit statuses, and the headless environment variables. Load before running, scripting, or parsing the output of any uniac command.
---

# The `uniac` CLI as an operational surface

The CLI is built for a caller that parses rather than reads. Two commands —
`deploy` and `status` — are **state gateways**: each writes exactly one state
document to stdout and says nothing about how it got there. Everything you need
to decide what to do next is in that document and the exit status.

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

## The output contract

This section is the contract of the two state-gateway commands, `deploy` and
`status`.

**Their stdout carries exactly one state document per run — nothing else, ever.**
Progress narration goes to stderr, only when stderr is a terminal, and it is
structurally incapable of reaching stdout. Force narration on with
`UNIAC_PROGRESS=1` (useful in CI), off with `UNIAC_PROGRESS=0`; neither changes
a byte of stdout.

A terminal is never consulted for the *document*: the same invocation through a
pipe and under a pty emits identical bytes.

### Encoding

Resolved in this order, first match wins:

1. `-o json` / `-o text` (also `--output`)
2. `UNIAC_OUTPUT=json|text`
3. an agent harness detected in the environment — any of `CLAUDECODE`,
   `AI_AGENT`, `AGENT`, `CODEX_SANDBOX`, `CURSOR_AGENT`, `GEMINI_CLI` set and
   non-empty → JSON
4. text

Detection is ergonomics, never contract. **Pass `-o json` explicitly whenever
you intend to parse.** The two encodings are information-equivalent — same
fields, same values, same precision — so a consumer that gets the unexpected
one has lost convenience, not facts.

### The document

`schema` is `"uniac/v1"`. Assert on it. It changes when a field's meaning
changes, never when a field is added, and absent facts are omitted rather than
zeroed — a document states only what the command actually established.

```json
{
  "schema": "uniac/v1",
  "ok": true,
  "command": "deploy",
  "project": "my-app-e5f6g7h8",
  "services": [
    {
      "name": "web",
      "version": 4,
      "image": "mendhak/http-https-echo:31",
      "digest": "sha256:…",
      "status": "running",
      "replicas": { "requested": 1, "effective": 1, "observed": 1 },
      "endpoints": [
        { "address": "https://<allocated-host>", "port": 8080, "type": "http" }
      ]
    }
  ],
  "duration_ms": 41230
}
```

| Field | Meaning |
|---|---|
| `ok` | Whether the command achieved what it was asked to do. |
| `command` | The verb that produced this document. |
| `project` | The linked project's slug. |
| `services[]` | One entry per service. A project is a flat list of services; the manifest's deployment is a client-side composition and never appears. |
| `services[].version` | Numbers the serving deployment — "which state is this service in". |
| `services[].image` | The source reference the manifest declared. Known only to a run that read the manifest. |
| `services[].digest` | The registry manifest digest this run published. |
| `services[].status` | The platform's word for what the service is doing. |
| `services[].replicas` | `requested` / `effective` / `observed`. |
| `services[].endpoints[]` | `address` is the whole string to dial; `port` is the service's own listen port that traffic lands on, which appears nowhere in `address`. |
| `services[].holds[]` | Platform-side reasons the service is not converging. |
| `services[].warnings[]` | Conditions the deploy succeeded despite — a dangling `${{...}}` reference shows up here. |
| `pending` | Present when the command returned before the platform finished: `deployment`, `task`, `step`, `poll_after_seconds`, and `next` — the literal command that resumes observation. |
| `error` | Present when `ok` is false: `code`, `message`, `retryable`, `holds`. |
| `duration_ms` | Wall time of the command. |

`http` endpoints are reached at `https://<hostname>`; `tcp` endpoints at
`<hostname>:<allocated-port>`. The allocated edge port is not a separate field —
for a tcp endpoint it is already the port inside `address`.

**A failed run still emits its document.** `ok:false` with a typed `error.code`,
plus whatever state the run did establish (a failed deploy still lists the
services it was working on). Never treat a non-zero exit as "no output".

## Exit statuses and error codes

Each code maps to exactly one status. **1 is deliberately unassigned** by the
state-gateway commands, so a bare `exit 1` from some future dependency can never
be mistaken for a meaning the CLI assigned.

| Exit | `error.code` | Meaning | What to do |
|---|---|---|---|
| 0 | — | Success. | Read `services[]`. |
| 2 | `usage` | Malformed invocation. Nothing was sent anywhere. | Fix the arguments. |
| 3 | `auth` | Missing or rejected credential. | `uniac auth login`, or set `UNIAC_ACCESS_TOKEN`. |
| 4 | `not_linked` | Directory not bound to a remote project. | `uniac link`, or set `UNIAC_PROJECT_URL`. |
| 5 | `manifest` | `uniac.yaml` does not describe a valid system. | Fix the manifest; `uniac plan` reproduces it offline. |
| 6 | `build` | Failed obtaining or materializing a container. | Check the image reference and the Docker daemon. |
| 7 | `push` | Failed publishing the image to the registry. | Usually retryable. |
| 8 | `deploy_failed` | The platform's deployment task failed. | Terminal unless `error.retryable` says otherwise. |
| 9 | `unreachable` | The platform did not answer; nothing was decided either way. | Retry with backoff. |
| 10 | `pending` | **Not a failure** — the work is still running; `pending` says how to resume. | Wait `poll_after_seconds`, then run `pending.next`. |
| 70 | `internal` | A defect in the CLI. | Report it with the message. |

Rules for consuming this:

- **Branch on the exit status; read `error.code` for detail.** Never match on
  `error.message` — prose is for people, and rewording it would silently change
  your behavior.
- **Never treat exit 10 as failure.** A consumer that does will abandon
  deployments that are about to succeed.
- **Treat any unrecognized code as internal.** The set is closed and additions
  are additive; surface the message rather than guessing.
- `retryable` is the platform's own judgment on whether re-running the identical
  command could succeed with nothing else changed. Prefer it to your own
  heuristics.
- **Read `error.message` on exit 70 before calling it a CLI defect.** As of
  v0.3.6 some conditions that have a code of their own still arrive as
  `internal`: an unlinked project directory reports `internal` rather than
  `not_linked`, and a platform failure during the link phase reports `internal`
  rather than `unreachable`. The message is accurate in both cases
  (`project not linked. Run \`uniac link\`…`, `cannot reach platform API at…`).

`plan`, `init`, `link`, and `auth` are **not** state-gateway commands: they are
human-oriented, print to stdout in their own shapes, and exit `1` on error, `2`
on a usage error. `uniac plan --json` emits `{resource, digest, deployable}` —
useful and stable, but not a `uniac/v1` document.

## Headless operation

| Variable | Effect |
|---|---|
| `UNIAC_ACCESS_TOKEN` | Bypasses interactive login. |
| `UNIAC_PROJECT_URL` | Targets a project by full URL or bare slug, bypassing `.uniac/deploy.json` and the interactive picker. |
| `UNIAC_OUTPUT` | `json` or `text` — the session default encoding. |
| `UNIAC_PROGRESS` | `1` forces stderr narration, `0` silences it. Never affects stdout. |
| `UNIAC_STORE_DIR` | Local artifact store location (default `~/.uniac/store`). |
| `UNIAC_AUTH_HOST` | The host serving the `/cli/auth` handoff (default `uniac.ai`). |

`UNIAC_ACCESS_TOKEN` + `UNIAC_PROJECT_URL` together are the fully headless path:
no picker, no browser. Without a link binding and without the override, `uniac
deploy` drops into the interactive project picker — which will hang a
non-interactive caller, so always set one of them in CI.

`.uniac/deploy.json` holds `{project_slug, project_name, gateway_url}` and is
per-checkout environment state, not source. Gitignore it.

## The loop an agent should run

```sh
uniac plan --json                          # offline; fix the manifest until this passes
uniac deploy -o json; echo $?              # branch on the status, read the document
uniac status -o json                       # re-observe at any time; changes nothing
```

Note the asymmetry: `plan` takes `--json` and has no `-o`; `deploy` and `status`
take `-o`/`--output` and have no `--json`. Passing the wrong one is a usage
error. `plan`, `deploy`, and `status` locate the project with `--dir`; `link`
uses `-C`.

`deploy` and `status` project the same facts through the same code, so what a
deploy reports and what an observation reports cannot drift into two accounts of
one system. When a deploy's account looks stale or incomplete, `uniac status` is
the authoritative re-read.
