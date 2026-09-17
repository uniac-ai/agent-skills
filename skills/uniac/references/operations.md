# Operations: the uniac CLI

Commands, destination selection, output and exit codes, compressed. Complete
contracts: [Uniac CLI](https://docs.uniac.ai/cli/overview.md),
[Authentication](https://docs.uniac.ai/cli/authentication.md),
[Output and errors](https://docs.uniac.ai/cli/output.md),
[Set up Uniac for your agent](https://docs.uniac.ai/setup.md).

## Install

`npm install -g @uniac/cli` (Node 18+), or `npx -y @uniac/cli …` without
installing. `uniac version` prints version, commit and build time. This
skill describes release 0.3.21.

## Commands

| Command | What it does | Needs |
|---|---|---|
| `uniac init` | Writes a starter `uniac.yaml` (one prebuilt-image service, deployment `main`) after prompting for a name; refuses if one exists. | Nothing |
| `uniac plan [--json] [--full] [--dir <path>]` | Validates the description and previews every deployment; `--json` prints `{project, digest, deployable, declarations}`. | Nothing |
| `uniac project create <name>` | Creates a project on the account; prints name and slug. | Credentials |
| `uniac link [-C <path>] [name-or-slug]` | Binds the local project to a remote one in `.uniac/deploy.json`; an exact slug or unique name skips the picker. | Credentials |
| `uniac deploy [--dir <path>]` | Plans, builds or pulls images with local Docker (`linux/amd64`), pushes, submits every declaration, polls each service up to five minutes. | Credentials, Docker |
| `uniac status [--dir <path>] [service]` | Reads the linked project's state; whole-project status also lists volumes. | Credentials, binding |
| `uniac auth login \| status \| token \| logout` | Browser sign-in; stored sessions and expiry; the selected credential; remove stored sessions. | — |

Flags may precede or follow the positional argument; a surplus argument is a
usage error. `-h` on any command prints its usage. There is no removal,
scaling, log or exec command. Removal and replica counts are dashboard
operations; neither the CLI nor the dashboard reads application logs or runs
commands in a container.

## Which project a command targets

- `plan`, `deploy`, `link` and `status` find the local project from the
  current directory: a containing `workspace` root, else the nearest
  `uniac.yaml`. A binding found below the root is an error.
- `.uniac/deploy.json` holds `project_name`, `project_slug`, `gateway_url`,
  `platform_url`; workspace packages share the root binding.
- `UNIAC_PROJECT_URL` (a gateway URL or slug) overrides the binding for
  `deploy`, but supplies no project name, so `status` cannot use it.
- `UNIAC_PLATFORM_URL` selects the platform API origin (default
  `https://api.uniac.ai`) for `project create`, `link` and `auth`; a linked
  `deploy`/`status` uses the binding's origin and fails on a conflict.
- Before image work, `deploy` checks the credential and that the bound
  project still matches by name, slug and gateway.

## Credentials

- `uniac auth login [--no-browser] [--manual] [--host <host>]` obtains a token
  through the website (account creation included) and stores it in
  `~/.uniac/auth.json` (mode 0600), one session per platform. It waits up to
  five minutes for the browser redirect.
- Selection order: a nonempty `UNIAC_ACCESS_TOKEN`, else the stored session
  for the addressed platform. A stored token stops being used 60 seconds
  before its expiry; nothing refreshes it — sign in again.
- `auth status` prints identities and expiry for every stored session (even
  expired); `auth token` prints the selected credential; `logout` deletes the
  stored sessions without revoking anything at the platform.

## What `deploy` does, in order

`plan` → `link` (credential and project check) → `build` (shared image work;
instances sharing a source share the build) → `push <service>` →
`submit <service>` (all services are registered before any is awaited) →
`observe <service>` (poll every two seconds, five-minute deadline). Failure
or interruption stops new local work; accepted remote work continues and
there is no rollback. A local release record is written under
`~/.uniac/store` (`UNIAC_STORE_DIR`).

## Output

- `deploy` and `status` print text to stdout; there is no JSON mode for
  them. Progress goes to stderr (`UNIAC_PROGRESS=1` plain lines, `0` off).
- Report rows: `project`, `platform` (only when not production), `root`,
  `service <name> [v<N>]`, `status <state> (observed/effective)`, `kind`,
  `lifecycle`, `deploying`, `replicas <N> requested`, `endpoint <type>
  <address> → :<container port>`, `volume <name> at <path>`, `hold`,
  `warning`; whole-project `status` adds `volume` blocks with size and state.
- Per-service `release` blocks record the submission outcome: `accepted`,
  `rejected`, `not attempted`, or `acceptance unconfirmed` (the server may
  have accepted it). `state unread` is a warning, not a failure.

## Exit codes

`deploy` and `status`: 0 success · 2 `usage` · 3 `auth` (no usable
credential, HTTP 401, or `status` without a project name) · 4 `not_linked`
(no or mismatched binding, no projects to pick) · 5 `manifest` (description
or ownership failure, missing build directory or Dockerfile) · 6 `build`
(Docker daemon, pull or build failure) · 7 `push` · 8 `deploy_failed`
(request or task failure, HTTP 403, observation deadline passed while work
continues) · 9 `unreachable` (transport errors and HTTP 502/503/504/521/522/
523/530) · 70 `internal`. Other commands: 0, 1 on failure, 2 on invalid
invocation; `plan` reports a description failure as 1.
