
# The `uniac` CLI as an operational surface

Two commands — `deploy` and `status` — are **state gateways**: once the
arguments parse, each leaves exactly one plain-text **final frame** on stdout
and says nothing else there. The command list, the flags-before-positionals
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
and no build arguments are injected. `uniac plan` never builds and never
contacts the Docker daemon, even for a `build:` service — it only checks that
the build root, context, and Dockerfile exist on disk.

The link phase resolves a supplied target — a `.uniac/deploy.json` binding or
`UNIAC_PROJECT_URL` — without contacting the platform, and the credential is
not validated until the first platform call, which comes after the build. So a
build failure reproduces offline with a throwaway slug and a dummy token.

`--full` adds each instance's declared env and start command to the preview's
text form; run `uniac plan --full` to see the shape. It shapes the text form
only — `uniac plan --json` carries `env` and `start_command` either way — and
the deployable *artifact* names the instance, never the definition it was drawn
from, though the `--full` text form names both.

Both `plan` and `deploy` target a **deployment** (resolution order in
[manifest.md](manifest.md)), and as of v0.3.12 it must instantiate exactly one
service: `plan` previews a multi-service deployment happily; `deploy` refuses
it with exit 5. `deploy` blocks until the platform's deployment task settles or
its deadline expires (minutes, not seconds), and reports what the service
settled as — registration alone is not success.

Flag parsing stops at the first non-flag token, and an *undefined* flag after
the positional is silently ignored too — `uniac plan main --nope` exits 0
rather than 2 — so a flag that had no effect is the only signal. Each command's
own flags are in `uniac <cmd> -h`.

## The output contract

There is no machine encoding to select: no `-o`/`--output` flag and no
`UNIAC_OUTPUT` variable exist, and passing `-o json` is a usage error. The text
frame is the output; the only JSON surface is `uniac plan --json` — the
deployable artifact, a different mechanism — emitting
`{resource, digest, deployable}`, whose keys are stable. Narration, the live
progress a run may emit while it is in flight, is a stderr concern only:
`UNIAC_PROGRESS` (see the environment table below) forces or silences it and
never changes stdout. A terminal is never consulted for the frame either — the
same run piped, captured, or under a pty leaves identical bytes on stdout
whatever the watch mode.

A `deploy` frame reports what the run did and, when a project was resolved, the
state that resulted. A failure carries its code on the frame's root line, and
marks that failure retryable there when it is; **`deploy` prints no error block
at all** — the code and the exit status are the machine contract. **A state
half is not evidence the platform was reached**: it appears once the link phase
has resolved a *named* project, so a purely local failure in a linked directory
still carries one.

`uniac status` writes the state alone, and it is the only command that prints
an error block. The state it reports is the state a deploy frame reports, so
when a deploy's account looks stale or incomplete, `uniac status` is the
authoritative re-read.

That state is a report for a human reader, not a wire format: branch on the
exit status rather than parsing it. **An omitted row is an absent fact, never a
hidden one** — two cases break that, and both are among the consumption rules
below. What the state reports, per service, is what the platform is running
*now*, not what was shipped: it carries no image reference and no digest.
Volume entities are reported only by a whole-project `uniac status` — never by
`uniac status <service>`, never by a deploy frame. Run `uniac status` against a
linked project to see which rows exist.

**A run that got past argument parsing still leaves its frame, pass or fail.**
The one exception is a usage error (exit 2) and `-h` (exit 0): both write only
to stderr and leave stdout empty.

## Exit statuses and error codes

Each code maps to exactly one exit status: `deploy` carries the code on its
frame's root line and prints no error block, `uniac status` carries it in its
error block, and in both the exit status is the same word. **1 is deliberately
unassigned** by the state-gateway commands, so a bare `exit 1` from some future
dependency can never be mistaken for a meaning the CLI assigned.

| Exit | `error` code | Meaning | What to do |
|---|---|---|---|
| 0 | — | Success. | Read the state it reports. |
| 2 | `usage` | Malformed invocation. Nothing was sent anywhere. | Fix the arguments. |
| 3 | `auth` | Missing credential for the platform the run addresses — none stored, or the stored one expired. | `uniac auth login`, or set `UNIAC_ACCESS_TOKEN`. |
| 4 | `not_linked` | Directory not bound to a remote project, or bound to a different platform than `UNIAC_PLATFORM_URL` selects. | `uniac link` — after `uniac project create <name>` when the account holds no projects; or unset the selector, or set `UNIAC_PROJECT_URL`. |
| 5 | `manifest` | `uniac.yaml` does not describe a valid system. | Fix the manifest; `uniac plan` reproduces most of these offline. |
| 6 | `build` | Failed obtaining or materializing a container — daemon, image reference, or the Dockerfile build itself. | Check the Docker daemon and the image reference; for a `build:` service, reproduce with `docker build`. |
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
  was doing when it was refused: most often exit 8, sometimes 7 or 70. A
  consumer that branches on exit 3 to re-authenticate never catches a revoked
  or wrong token, and loops forever on a project it cannot name.
- **Exit 8 from `uniac status` means the read was refused, not that a
  deployment failed.** The read that decides the command is the project listing
  for a whole-project run and the per-service read for
  `uniac status <service>`. A platform that did not answer that read at all is
  exit 9, not 8.
- **Two cases break *an omitted row is an absent fact*.** A deploy that could
  not read the service's state back says so in a warning. A whole-project
  `uniac status` whose additive per-service or volumes read was refused says
  nothing at all and still exits 0 — the facts those reads would have carried
  are simply missing, and no row admits it. `uniac status <service>` makes no
  additive read, so the same refusal there is exit 8.
- `retryable` is the platform's own judgment on whether re-running the
  identical command could succeed with nothing else changed. Prefer it to your
  own heuristics.
- **Read the message on exit 70 before calling it a CLI defect.** As of
  v0.3.14 exit 10 is reserved but unreached — a deploy that outlives its
  deadline arrives as exit 8. Exit 4 is real: `deploy` raises it when the
  account holds no projects, and both state gateways raise it before any
  network call when the directory's binding and an explicit
  `UNIAC_PLATFORM_URL` name different platforms. An unlinked directory is
  still exit 3 when no credential is stored, or 70 with one — never 4.

`plan`, `init`, `project`, `link`, and `auth` are **not** state-gateway
commands: they are human-oriented and exit `1` on error, `2` on a usage
error. `plan`, `init`, `project create`, and `auth` print their results to
stdout; `link` writes its listing, its prompt, and its confirmation to
stderr and leaves stdout empty.

## Headless operation

| Variable | Effect |
|---|---|
| `UNIAC_ACCESS_TOKEN` | Bypasses interactive login. |
| `UNIAC_PROJECT_URL` | Targets a project by full URL or bare slug, bypassing `.uniac/deploy.json` and the interactive picker. `deploy` only — see below. |
| `UNIAC_PLATFORM_URL` | Platform gateway origin for the entry actions — `auth login`, `project create`, `link` (default `https://api.uniac.ai`). Operations in a linked directory follow the binding's recorded platform instead; an explicit value contradicting the binding exits 4 naming both. |
| `UNIAC_PROGRESS` | `1` forces stderr progress lines, `0` silences them. Never affects stdout. |
| `UNIAC_AUTH_HOST` | The host serving the `/cli/auth` handoff. The default platform signs in at `uniac.ai`; any other `UNIAC_PLATFORM_URL` requires this set — the CLI never derives a sign-in host from a platform's name. |
| `UNIAC_STORE_DIR` | Root of the local artifact store (default `~/.uniac/store`), the directory `uniac deploy` writes each run's release record under. |

`UNIAC_ACCESS_TOKEN` + `UNIAC_PROJECT_URL` together are the fully headless
**deploy** path: no picker, no browser. Without a link binding and without the
override, `uniac deploy` drops into the interactive project picker; unattended
it fails fast rather than wedging. Set one of the two in CI because the run
cannot otherwise succeed, not because it would hang.

**`uniac status` cannot use the override.** An override names a target but not
a project, and `status` reads by project name — so the override, which wins
over the binding, leaves it with no name to read by. Even in a linked
directory it then fails with exit 3 and a misleading not-linked message, which
points at the wrong fix. Observation needs the real link binding: run
`uniac link` once, and unset `UNIAC_PROJECT_URL` when running `status`.

`.uniac/deploy.json` holds
`{project_slug, project_name, gateway_url, platform_url}` — the binding
records everything operations on the directory need, its platform included,
so a linked directory never resolves its platform from the environment.
Sessions in `~/.uniac/auth.json` are likewise stored per platform, keyed by
platform gateway origin: signing in to one platform never disturbs a session
held for another, and acting where no session is stored exits 3 naming the
platform.
