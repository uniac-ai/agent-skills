# Operations: the uniac CLI

Commands, destination selection, output and exit codes, compressed. Complete
contracts: [Uniac CLI](https://docs.uniac.ai/cli/overview.md),
[Authentication](https://docs.uniac.ai/cli/authentication.md),
[Output and errors](https://docs.uniac.ai/cli/output.md),
[Set up Uniac for your agent](https://docs.uniac.ai/setup.md).

## Install

`npm install -g @uniac/cli` (Node 18+), or `npx -y @uniac/cli …` without
installing. `uniac version` prints version, commit and build time. This
skill describes release 0.3.32.

## Commands

| Command | What it does | Needs |
|---|---|---|
| `uniac init` | Writes a starter `uniac.yaml` (a prebuilt-image definition `<name>-definition` and its deployment declaration `<name>`) after prompting for the service name; refuses if one exists. | Nothing |
| `uniac plan [--json] [--full] [--dir <path>]` | Validates the description and previews every deployment; `--json` prints `{project, digest, deployable, declarations}`. | Nothing |
| `uniac project create <name>` | Creates a project on the account; prints name and slug. | Credentials |
| `uniac link [-C <path>] [name-or-slug]` | Binds the local project to a remote one in `.uniac/deploy.json`; an exact slug or unique name skips the picker. | Credentials |
| `uniac deploy [--dir <path>]` | Plans, builds or pulls images with local Docker (`linux/amd64`), pushes, submits every declaration, polls each service's deployment until it succeeds or fails, up to five minutes. | Credentials, Docker |
| `uniac status [--dir <path>] [service]` | Reads the linked project's state; whole-project status also lists volumes. | Credentials, binding |
| `uniac logs <service> [--instance <id>] [-f] [--previous] [--tail <n>] [--since <time>] [--dir <path>]` | Prints what the service's instances write, each line prefixed with its instance; `-f` follows them until interrupted. | Credentials, binding |
| `uniac service delete <name> [--dir <path>] [--silent]` | Deletes a service and waits until the platform has removed it (five-minute deadline); its volume is unbound and keeps its data. | Credentials, binding |
| `uniac volume delete <name> [--dir <path>] [--silent]` | Deletes a volume no service is bound to, and its data, and waits until the platform has removed it (five-minute deadline); `<name>` is `<service>.<volume>` as `status` lists it. | Credentials, binding |
| `uniac project delete <name> [--silent]` | Deletes a project with its services, endpoints and every volume and its data, unbound ones included; returns once the platform accepts the deletion. | Credentials |
| `uniac auth login \| status \| token \| logout` | Browser sign-in; stored sessions and expiry; the selected credential; remove stored sessions. | — |

Flags may precede or follow the positional argument; a surplus argument is a
usage error. `-h` on any command prints its usage. The dashboard sets replica
counts and changes public endpoints
([Dashboard and removal](https://docs.uniac.ai/resources/service.md#dashboard-and-removal)).

## Which project a command targets

- `plan`, `deploy`, `link`, `status`, `logs` and the service and volume
  deletes find the local project from the current directory: a containing `workspace` root, else the
  nearest `uniac.yaml`. Above the project, only a `uniac.yaml` that declares
  `workspace` counts. A binding found below the root is an error.
- `.uniac/deploy.json` holds `project_name`, `project_slug`, `gateway_url`,
  `platform_url`; workspace packages share the root binding.
- `UNIAC_PROJECT_URL` (a gateway URL or slug) replaces the binding as the
  destination of `deploy`, `status`, `logs` and the service and volume
  deletes: the
  CLI finds the project in the account's project list, so `deploy` waits for its services and `status`
  reads it. A value naming no project on the account exits 4.
- `UNIAC_PLATFORM_URL` selects the platform API origin (default
  `https://api.uniac.ai`) for `project create`, `project delete`, `link` and
  `auth`; a linked `deploy`, `status` or `logs` uses the binding's origin and
  fails on a conflict.
- Before image work, `deploy` checks the credential and that the bound
  project still matches by name, slug and gateway.

## Credentials

- `uniac auth login [--no-browser] [--manual] [--host <host>]` obtains a token
  through the website (account creation included), checks it with the
  platform, and stores it in `~/.uniac/auth.json` (mode 0600), one session per
  platform. A platform accepts only its own sign-in website's tokens; one it
  rejects fails the login and keeps the stored session. It waits up to five
  minutes for the browser redirect.
- Selection order: a nonempty `UNIAC_ACCESS_TOKEN`, else the stored session
  for the addressed platform. A stored token stops being used 60 seconds
  before its expiry; `uniac auth login` stores a new one.
- `auth status` prints each stored session's platform, issuer, identity and
  expiry, and whether that platform accepts it (expired sessions are not
  checked); it exits 1 when a platform rejects its session. `auth token`
  prints the selected credential; `logout` removes the
  stored sessions from this machine, and tokens already issued, including one
  set as `UNIAC_ACCESS_TOKEN`, stay valid at the platform until they expire.

## What `deploy` does, in order

`plan` → `link` (credential and project check) → `build` (shared image work;
services sharing a source share the build) → `push <service>` →
`submit <service>` → `observe <service>` (poll every two seconds,
five-minute deadline), in reference order: a service is submitted after the
declared services it references have settled, and services with no reference
between them are submitted together before any is awaited. Failure,
interruption or the five-minute deadline stops new local work, so services
after it in reference order are not attempted, and accepted remote work
continues; to return to an
earlier release, deploy that release's sources or images again.
A local release record is written under `~/.uniac/store` (`UNIAC_STORE_DIR`).

## Deleting

- In a terminal, `service delete`, `volume delete` and `project delete` show
  what they delete and ask for the typed name; another answer deletes nothing
  (exit 2). `--silent` skips the question and changes nothing else. Without a
  terminal, `--silent` is required, or the command exits 2 before any request.
- `service delete` and `volume delete` poll until what they delete is gone;
  after the deadline (exit 10) or an interruption the platform continues the
  deletion, and `uniac status` shows the service as `terminating` or the
  volume as `deleting`. A volume is gone once its storage is released. The
  platform refuses to delete a volume a service is bound to (exit 8).
- `project delete` returns once the platform accepts the deletion; the
  platform then removes the services, endpoints and volumes, and
  `project create` accepts the name again once it has. A repeated
  `project delete` finds no project of that name (exit 8). A directory linked
  to the deleted project keeps its binding, and `deploy` and `status` there
  exit 4 until `uniac link` selects another project. An agent deletes a
  project only when its user asks for it.
- Success prints `Deleted service <name> from project <project>.` (plus the
  kept volume), `Deleted volume <name> and its data from project <project>.`,
  or `Deleted project <name>.` and that the platform finishes removing its
  services, endpoints and volumes; failure prints the `status` error block.
  [Deleting services, volumes and projects](https://docs.uniac.ai/cli/overview.md#deleting-services-volumes-and-projects).

## Reading logs

- stdout gets `[<instance>] <line>` for every line, stdout or stderr alike;
  `<instance>` is the first 8 characters of the instance's key, more where
  two of the service's instances share them. The pruned-output notice
  (`earlier output was pruned before it could be read`), `Service <name> has
  no instances.` (exit 0) and error blocks go to stderr.
- Without `-f`: each instance's current run, one instance after another in
  key order, then exit. `--previous` reads the run before it (not with `-f`;
  an instance without one fails, exit 8). `--tail <n>` (0–100000) and
  `--since <RFC 3339>` narrow each run. `--instance` takes a key or a start
  of one that no other instance shares.
- `-f` follows the instances the service has when it starts, at once, across
  restarts. The platform ends a followed read every five minutes and the CLI
  resumes it without losing or repeating a line, as after a dropped
  connection; a moved instance continues on its new node, a removed one's
  output ends, and an instance whose logs stay unavailable through five
  minutes of retries exits 9. An expired credential ends it with exit 3.
  Interrupting exits 0.
- An account holds 10 open reads and an instance 4, one per instance being
  read; beyond that the read fails (exit 8) naming the limit.
- One instance's failure prints its error block and the others go on; the
  exit code is the first failed instance's.
  [Reading logs](https://docs.uniac.ai/cli/overview.md#reading-logs),
  [Log output](https://docs.uniac.ai/cli/output.md#log-output).

## Output

- `deploy` and `status` print text reports to stdout. Progress goes to
  stderr (`UNIAC_PROGRESS=1` plain lines, `0` off).
- Report rows: `project`, `platform` (shown for platforms other than production), `root`,
  `service <name> [v<N>]`, `status <state> (observed/effective)` (the counts
  when the observed count is reported), `kind`, `size <N> vCPU, <M> MiB`,
  `lifecycle`, `deploying`, `replicas <N> requested`, `instance <status>`
  (one per instance, then `, started <RFC 3339 UTC>` once its container
  started; none for a service without instances), `endpoint <type>
  <address> → :<container port>`, `volume <name> at <path>`, `hold`,
  `warning`; `deploy` and whole-project `status` add the project's `volume`
  blocks, unbound volumes included, with `size <N>GiB` (while a growth is
  pending, `<N>GiB, growing to <M>GiB since <RFC 3339 UTC>`, the time when
  the platform recorded it) and `state` (`bound to <service>`,
  `available (no service is bound; data intact)`, `provisioning`,
  `releasing`, `deleting`).
- Per-service `release` blocks record the submission outcome: `accepted`,
  `rejected`, `not attempted`, or `acceptance unconfirmed` (the server may
  have accepted it). `state unread` is reported as a warning. Warnings leave
  the exit code unchanged, and a name-only `service` row means the service's
  state was not read.

## Exit codes

`deploy`, `status`, `logs`, `service delete`, `volume delete` and
`project delete`: 0 success · 2
`usage` (also a delete without `--silent` or a terminal, a mismatched
typed name, or `logs -f --previous`) · 3 `auth` (no usable
credential or HTTP 401) · 4 `not_linked` (no or mismatched binding, a
`UNIAC_PROJECT_URL` naming no project, no projects to pick) · 5 `manifest` (description
or ownership failure, missing build directory or Dockerfile) · 6 `build`
(Docker daemon, pull or build failure) · 7 `push` · 8 `deploy_failed`
(request or task failure, HTTP 403 or another refused platform read, a
refused delete such as a missing service or project or a volume a service is
bound to, a refused log read or an `--instance` matching no instance or
several)
· 9 `unreachable` (transport errors and HTTP 502/503/504/521/522/523/530, or
an instance's logs unavailable through five minutes of retries) ·
10 `pending` (`deploy`, `service delete` or `volume delete` stopped observing
work the platform is still doing, after five minutes; nothing had failed by
then, and later services in reference order were not attempted) · 70
`internal`. Other commands: 0, 1 on failure, 2 on invalid
invocation; `plan` reports a description failure as 1.
