
# The `uniac` CLI as an operational surface

Two commands — `deploy` and `status` — are **state gateways**: once the
arguments parse, each leaves exactly one plain-text **final frame** on stdout
and says nothing else there. The command table, the flags-before-positionals
rule, the `auth -h` hazard, and the environment requirements live in the skill
body; this document is the contract beneath them.

## Command behavior

`deploy` needs a running Docker daemon for both sources. A service declaring
`image:` is pulled locally with **your own** docker credentials (`config.json`
and its helpers, exactly like `docker pull`); a service declaring `build:` is
built locally from your project tree. Either way the resulting image is pushed
to the project registry, and the two paths are identical from there on. A
private base image your local docker cannot pull fails the build phase.
Builds always target `linux/amd64` regardless of host architecture, and run on
every deploy — nothing is cached between runs beyond docker's own layer cache,
and no build arguments are injected. A build reports as one board step labelled
`build .`, or `build ./<root>` when the source names a root; the `build`
phase's exit status is 6. `uniac plan` never builds and never contacts the
Docker daemon, even for a `build:` service — it only checks that the build
root, context, and Dockerfile exist on disk.

`--full` adds the declaration details to the `Deploying` rows and changes
nothing else: the `Deployment:` and `Artifact:` lines and the whole `Building`
section are identical. An instance's row gains `from <definition>` in the
parentheses after its name when the instance name differs from the definition
it came from, absent when the names match, then an indented `start:` sub-row
when it declares a start command and an `env:` sub-row listing its variables
one per line, sorted by name. Plain, then `--full`, on one manifest:

```
Deploying
  database (stateful)  postgres:17-alpine            volume: database.data (20GB)
  frontend             mendhak/http-https-echo:31  public: 8080 (http)
```

```
Deploying
  database (stateful, from db)  postgres:17-alpine    volume: database.data (20GB)
    start: postgres -c max_connections=200
    env:
      PGDATA=/var/lib/postgresql/data/pgdata
  frontend (from web)  mendhak/http-https-echo:31  public: 8080 (http)
    env:
      GREETING=hello
```

`--full` shapes the text form only for the two declaration details the
deployable carries: `uniac plan --json` has `env` and `start_command` either
way. `from <definition>` is display-only — the deployable names the instance,
never the definition it was drawn from.

Both `plan` and `deploy` target a **deployment** (resolution order in
[manifest.md](manifest.md)), and as of v0.3.12 it must instantiate exactly one
service: `plan` previews a multi-service deployment happily; `deploy` refuses
it with exit 5 and `deployment "<name>" instantiates <N> services;
multi-service deployments are not yet supported`. `deploy` blocks while the
platform's deployment task runs, polling every 2s for up to 5 minutes, and
reports what the service settled as — registration alone is not success.

Flag parsing stops at the first non-flag token, and an *undefined* flag after
the positional is silently ignored too — `uniac plan main --nope` exits 0
rather than 2 — so a flag that had no effect is the only signal. `plan`,
`deploy`, and `status` locate the project with `--dir`; `link` uses `-C`.

## The output contract

There is no machine encoding to select: no `-o`/`--output` flag and no
`UNIAC_OUTPUT` variable exist, and passing `-o json` is a usage error. The
text frame is the output; the only JSON surface is `uniac plan --json` — the
deployable artifact, a different mechanism. A terminal is never consulted for
the frame: the same run piped, captured, or under a pty leaves identical bytes
on stdout whatever the watch mode.

### The final frame

The frame is what remains of the run's task tree, in two registers: the **run
record** — what the run did — and the **output** — what it established,
following a blank line and rendered at the left margin because it is the
answer, not a step.

**A success frame** is the root line plus its immediate stages as one-liners,
one level deep and never deeper — nested subtasks (the build's per-image
pulls) never appear. The stages are `plan`, `link`, `build`, `push <service>`,
and `deploy <service>`; a stage may carry a summary after its label, and a
duration in parentheses only when it took a second or more (the root line
always carries one).

```
✓ deploy main  (1.6s)
  ✓ plan  sha256:be4ee43ed10b
  ✓ link  my-app-e5f6g7h8
  ✓ build  1 image(s)  (1.4s)
  ✓ push web  sha256:d1a8d0a4eeb6
  ✓ deploy web  running

project  Scratch Project

service     web  v4
  status    running (1/1)
  endpoint  http  https://kq7wn2xr4m1v.svc.uniac.ai → :8080
```

**A failure frame** carries the failure class on the root line and expands only
the path to the failure: completed siblings stay one-liners, the broken stage
expands, and the node where the failure actually happened prints its retained
evidence inset two further levels. When the failure is retryable the root line
says so: `✗ deploy main  push — retryable  (1.8s)`. **`deploy` prints no
`error`/`message`/`retryable` block at all** — the root-line code and the exit
status are the machine contract:

```
✗ deploy main  build  (328ms)
  ✓ plan  sha256:fc0252a4b82f
  ✓ link  scratch-proj
  ✗ build
      ✗ pull ghcr.io/uniac-ai/does-not-exist:1.0  (328ms)
      image-pull[{"Platform":"linux/amd64","Ref":"ghcr.io/uniac-ai/does-not-exist:1.0"}]: pull ghcr.io/uniac-ai/does-not-exist:1.0: Error response from daemon: error from registry: denied
      denied

project  Scratch Project
```

**The output is omitted entirely when the run established nothing.** A run that
never reached the platform — an auth or manifest failure — is the record alone,
with no trailing blank line:

```
✗ deploy main  auth  (0ms)
  ✓ plan  sha256:fc0252a4b82f
  ✗ link
      resolving deploy target
      no access token found. Run `uniac auth login` or set UNIAC_ACCESS_TOKEN
```

The root label gains the target only once resolution succeeds, so every
failure raised by resolution itself keeps the bare `deploy` — including the
composition failures whose own message names the deployment:

```
✗ deploy  manifest  (0ms)
  ✗ plan
      deployment "main": service "api": env DB references store.MISSING, but "store" declares no such variable (available: host, PGDATA)
```

The one `manifest`-coded failure that shows a target is the multi-service
rejection, raised after resolution succeeded: `✗ deploy main  manifest  (0ms)`.
So the label is a fact about how far the run got, never a hint about what went
wrong — read the code, not the label.

**`uniac status` writes the state block alone**, and when it failed, a blank
line and the error block. Its state block is byte-for-byte the rendering a
deploy frame's output uses, so when a deploy's account looks stale or
incomplete, `uniac status` is the authoritative re-read.

### The state block

The state block is `key  value` rows, sub-rows indented two spaces, sections
separated by blank lines. **An omitted row is an absent fact, never a hidden
one.** Rows appear in this fixed order:

```
project  <name>

service  <name>  v<N>
  status  <status> (<observed>/<effective>)
  kind  <stateful|stateless>
  lifecycle  <phase>
  deploying  <task state>: <step>
  replicas  <N> requested
  endpoint  <type>  <address> → :<port>
  volume  <entity-name> at <mount-path>
  hold  <reason>
  warning  <condition>

volume  <name>
  size  <N>GB
  state  <line>
```

**There is no `image` row and no `digest` row** — a run's declared image
reference and published digest are not part of this account.

- One `service` section per service; the manifest's deployment never appears.
- `project` is the project name the link binding carries. `deploy` falls back
  to the slug when the binding has no name; `status` has no fallback — it
  cannot read a project it cannot name, and fails with `auth` instead.
- `v<N>` numbers the serving deployment, present only once the platform has
  one. `status` is the platform's word for what the service is doing; the
  `(observed/effective)` replica count appears when the platform reported one.
- `kind` is the platform's word for how it runs the service's instances —
  `stateful` for one capped at a single instance, `stateless` otherwise. The
  row is omitted only when the platform reported no kind at all, so its
  presence alone does not mean stateful.
- `lifecycle` is the serving deployment's phase, printed only when it says
  something — `active` is the quiet normal and prints nothing. `deploying`
  names the deployment task in flight (e.g. `running: attaching volume`),
  absent when nothing is running. `replicas` appears only when the requested
  count differs from the effective one.
- `endpoint`: the ingress kind (`http` or `tcp`) is stated outright, then the
  whole string to dial, then your own listen port the traffic lands on — which
  appears nowhere in the address. One row per public address.
- `volume` links the service to a durable volume it mounts: the composed
  entity name and the mount path. It carries no size and no lifecycle.
- `hold` rows are platform-side reasons the service is not converging.
  `warning` rows are conditions the run succeeded despite, and they come from
  three places: the platform's own conditions on the deployment task — a
  dangling `${{...}}` reference is one — reach both commands, and the other
  two only a `deploy` can add: `release record not written: <err>` when the
  local release record could not be written, and `` state unread — the platform
  read path did not answer; run `uniac status` `` when the run finished but
  could not read that service's state back.
- Under `state unread` the service's remaining rows are missing because
  **nothing was read**, not because the platform reported empty — the section
  is the service name and its warning rows, and no `status`, `v<N>`, or
  `endpoint` fact is being asserted either way.
- `volume` **entity sections** — name, size, state — appear only in
  whole-project `uniac status`; `uniac status <service>` and a deploy frame
  never show them. State reads `attached to <service>`, or bare `attached`
  with no holder, or `unattached (no service holds it; data intact)`, or the
  platform's own word for a transitional state (`provisioning`, `attaching`,
  `detaching`, `deleting`).

Columns are aligned per block, so the key-column width differs between two
service sections in one run. **Split on runs of spaces, never on a fixed
column.** A real whole-project read:

```
project  Scratch Project

service     excalidraw  v3
  status    running (1/1)
  kind      stateless
  endpoint  http  https://excalidraw-scratch.svc.uniac.ai → :80

service      postgres  v7
  status     degraded (0/1)
  kind       stateful
  lifecycle  preparing
  deploying  running: attaching volume
  replicas   2 requested
  endpoint   tcp  tcp.uniac.ai:31544 → :5432
  volume     postgres.pgdata at /var/lib/postgresql/data
  hold       waiting for volume postgres.pgdata to attach
  warning    image has no healthcheck

volume   postgres.pgdata
  size   20GB
  state  attached to postgres

volume   old-cache.data
  size   5GB
  state  unattached (no service holds it; data intact)
```

### The error block — `uniac status` only

Only `uniac status` prints it, after the state block and a blank line. When
nothing was read the state block is empty and stdout therefore begins with a
bare newline:

```

error      auth
  message  no access token found. Run `uniac auth login` or set UNIAC_ACCESS_TOKEN
```

Row keys are `error`, `  message`, and `  retryable  yes` — the last present
only when retryable. A multi-line message keeps the block's shape: continuation
lines get an empty key column, and `retryable` stays attached as its own row.

```
project  Broken Project

error        unreachable
  message    read project Broken Project: GET /api/projects/Broken%20Project returned 530: origin is unreachable
             error code: 1016
             ray id: 8f3c2a91
  retryable  yes
```

**A run that got past argument parsing still leaves its frame, pass or fail.**
The one exception is a usage error (exit 2) and `-h` (exit 0): both write only
to stderr and leave stdout empty.

### Watching a run

Live rendering is a stderr concern. The decision reads only physical facts
about stderr — it never inspects who spawned the shell, and the binary contains
no agent-harness variable names at all. First match wins:

1. `UNIAC_PROGRESS=0` — silent.
2. `UNIAC_PROGRESS=1` — plain progress lines streamed to stderr as they happen
   (the CI-log form). Only `0` and `1` are recognized, surrounding whitespace
   trimmed; any other value falls through.
3. stderr is not a terminal — silent.
4. stderr is a terminal but reports no usable width — silent.
5. Otherwise — a live task tree repaints on stderr and is erased when the run
   ends.

Rendering starts only once linking can no longer prompt, so a run that fails at
the plan or link step emits nothing to stderr even with `UNIAC_PROGRESS=1`.
Once it does start, the stream replays the stages already finished, so `plan`
and `link` appear in the log of every run that got past them:

```
deploy main
  plan
  ✓ plan  sha256:fc0252a4b82f
  link
    resolving deploy target
  ✓ link  scratch-proj
  build
    pull ghcr.io/uniac-ai/does-not-exist:1.0
```

## Exit statuses and error codes

Each code maps to exactly one status: `uniac deploy` carries the code on its
root line (`✗ deploy main  build  (328ms)`) and prints no error block,
`uniac status` carries it in the `error` row of its error block, and in both
the exit status is the same word. **1 is deliberately unassigned** by the
state-gateway commands, so a bare `exit 1` from some future dependency can
never be mistaken for a meaning the CLI assigned.

| Exit | `error` code | Meaning | What to do |
|---|---|---|---|
| 0 | — | Success. | Read the state block. |
| 2 | `usage` | Malformed invocation. Nothing was sent anywhere. | Fix the arguments. |
| 3 | `auth` | Missing credential — none stored, or the stored one expired. | `uniac auth login`, or set `UNIAC_ACCESS_TOKEN`. |
| 4 | `not_linked` | Directory not bound to a remote project. | `uniac link`, or set `UNIAC_PROJECT_URL`. |
| 5 | `manifest` | `uniac.yaml` does not describe a valid system. | Fix the manifest; `uniac plan` reproduces most of these offline. |
| 6 | `build` | Failed obtaining or materializing a container. | Check the image reference and the Docker daemon. |
| 7 | `push` | Failed publishing the image to the registry. | Usually retryable. |
| 8 | `deploy_failed` | The platform refused the operation — a deployment task that failed, or a read it declined. | Terminal unless `retryable` says otherwise. |
| 9 | `unreachable` | The platform did not answer; nothing was decided either way. | Retry with backoff. |
| 10 | `pending` | **Not a failure** — the work is still running. | Re-observe with `uniac status`. |
| 70 | `internal` | A defect in the CLI. | Report it with the message. |

Rules for consuming this:

- **Branch on the exit status; read the code for detail.** Never match on the
  message — prose is for people, and rewording it would silently change your
  behavior.
- **Never treat exit 10 as failure.** A consumer that does will abandon
  deployments that are about to succeed.
- **Treat any unrecognized code as internal.** The set is closed and additions
  are additive; surface the message rather than guessing.
- **A credential the platform *rejects* is not `auth`.** Exit 3 is a credential
  the CLI has no usable copy of, or a `status` with no project name to read by
  — a working token changes neither. A rejection lands under whatever the run
  was doing when it was refused: the registration — a deploy's
  `deploy <service>` stage — and the read that decides a `uniac status` give
  exit 8; the `push <service>` stage gives exit 7; and an unlinked directory's
  `link` stage, whose project listing is the only platform call that stage
  makes, gives exit 70 — `✗ deploy main  internal`, with the 401 inset under
  `link`. A consumer that branches on exit 3 to re-authenticate never catches
  a revoked or wrong token, and loops forever on a project it cannot name.
- **Exit 8 from `uniac status` means the read was refused, not that a
  deployment failed.** The read that decides the command is the project listing
  for a whole-project run and the per-service read for
  `uniac status <service>`. Every status the platform answers *that* read with
  lands at 8 — 401, 403, 404 and 500 alike — except the edge statuses 502, 503,
  504, 521, 522, 523 and 530 and a transport error, which are exit 9.
- **A whole-project `uniac status` swallows its other two reads' refusals** —
  both additive, both exit 0, with no error block and no `warning` row. A
  per-service detail it cannot read costs that service its `v<N>`, `kind`,
  `lifecycle`, `deploying`, `replicas`, `endpoint`, `volume` and `hold` rows —
  the section keeps the name and the `status` the listing carried — and a
  refused volumes read costs every volume entity section. This is where *an
  omitted row is an absent fact* does not hold: those rows were never read,
  and nothing in the output says so. `uniac status <service>` makes no
  additive read, so the same refusal there is exit 8.
- `retryable` is the platform's own judgment on whether re-running the
  identical command could succeed with nothing else changed. Prefer it to your
  own heuristics.
- **Read the message on exit 70 before calling it a CLI defect.** As of
  v0.3.12, exits 4 and 10 are reserved but nothing produces them: `deploy`
  watches its deployment task to settlement (a deadline expiry arrives as exit
  8, `deploy <service>: still <step> after 5m0s — check the dashboard`, where
  `<step>` is the active step's label, its key when the platform gives no
  label, and only then the task state), and an unlinked directory arrives as
  exit 3 when no credential is stored. With one stored, `status` exits 70 with
  ``project not linked. Run `uniac link` or set UNIAC_PROJECT_URL``, while
  `deploy` opens the interactive picker instead — unattended (stdin at EOF)
  that is exit 70 with `no selection made`.

`plan`, `init`, `link`, and `auth` are **not** state-gateway commands: they are
human-oriented and exit `1` on error, `2` on a usage error. `plan`, `init`, and
`auth` print their results to stdout; `link` puts its listing, its prompt, and
its `Linked to …` confirmation on stderr and leaves stdout empty.
`uniac plan --json` emits `{resource, digest, deployable}` — useful and stable.

## Headless operation

| Variable | Effect |
|---|---|
| `UNIAC_ACCESS_TOKEN` | Bypasses interactive login. |
| `UNIAC_PROJECT_URL` | Targets a project by full URL or bare slug, bypassing `.uniac/deploy.json` and the interactive picker. `deploy` only — see below. |
| `UNIAC_PROGRESS` | `1` forces stderr progress lines, `0` silences them. Never affects stdout. |
| `UNIAC_AUTH_HOST` | The host serving the `/cli/auth` handoff (default `uniac.ai`). |
| `UNIAC_STORE_DIR` | Root of the local artifact store (default `~/.uniac/store`), the directory `uniac deploy` writes each run's release record under. |

`UNIAC_ACCESS_TOKEN` + `UNIAC_PROJECT_URL` together are the fully headless
**deploy** path: no picker, no browser. Without a link binding and without the
override, `uniac deploy` drops into the interactive project picker; unattended
it fails fast rather than wedging — stdin at EOF ends the prompt at once (the
exit-70 note above), and only a pipe held open by something that never writes
blocks. Set one of the two in CI because the run cannot otherwise succeed, not
because it would hang.

**`uniac status` cannot use the override.** An override names a target but not
a project, and `status` reads by project name — so the override, which wins
over the binding, leaves it with no name to read by. Even in a linked
directory it then fails with exit 3 and the misleading message
``this directory is not linked to a project. Run `uniac link` first``.
Observation needs the real link binding: run `uniac link` once, and unset
`UNIAC_PROJECT_URL` when running `status`.

`.uniac/deploy.json` holds `{project_slug, project_name, gateway_url}`.
