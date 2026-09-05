# CLI

`uniac …` can run as `npx -y @uniac/cli …` with Node ≥ 18, or through a
global installation from `npm i -g @uniac/cli`.

For commands accepting positional arguments, parsing stops at the first
positional argument; trailing flags are ignored. `uniac -h` lists commands
and `uniac <command> -h` lists flags.

## Commands

| Command | Effect |
|---|---|
| `init` | Writes a starter `uniac.yaml` with one prebuilt-image service and its deployment. Offline; takes defaults when unattended. `npm create @uniac@latest` invokes it. |
| `plan [deployment]` | Resolves a manifest deployment. Requires no credentials, network, or Docker. |
| `project create <name>` | Creates a remote project. |
| `link [name-or-slug]` | Creates or replaces a directory's binding to an existing project. The directory must contain `uniac.yaml`. Omitting the argument opens a project picker. |
| `deploy [deployment]` | Requests deployment of the selected manifest declaration. |
| `status [service]` | Reads current state for a linked project, including services absent from the local manifest, or one named service. |
| `auth login` | Starts browser sign-in, with account creation available, and stores the resulting session. Reports whether the browser opened and prints the sign-in URL. Sign-in requires the user's browser interaction. |
| `auth status` | Reads stored sessions and their expiry locally. Does not validate credentials or inspect `UNIAC_ACCESS_TOKEN`. |
| `auth token` | Prints the selected access token. |
| `auth logout` | Removes all stored platform sessions. |
| `version` | Prints the installed version. |

The CLI has no removal command.

## Authentication

`project create`, `link`, `deploy`, and `status` require authentication.
Sessions are stored per platform in `~/.uniac/auth.json`. A stored token
becomes unusable 60 seconds before its recorded expiry. The CLI does not
refresh it automatically.

| Variable | Meaning |
|---|---|
| `UNIAC_ACCESS_TOKEN` | Access token for the selected platform; takes precedence over stored tokens. |
| `UNIAC_PLATFORM_URL` | Platform API origin for login, `auth token`, project creation, linking, and target overrides. Default: `https://api.uniac.ai`. |
| `UNIAC_AUTH_HOST` | Browser sign-in host. Defaults to `uniac.ai` for the default platform; required for another platform unless login's `--host` is supplied. |

## Project selection

`link` writes `.uniac/deploy.json`, containing
`{project_slug, project_name, gateway_url, platform_url}`. The deploy project
picker can also write this binding.

`UNIAC_PROJECT_URL` supplies a gateway URL or project slug, overriding the
binding without supplying a project name. Without this override, `deploy`
and `status` use the binding's platform; a conflicting `UNIAC_PLATFORM_URL`
fails before a network call.

Without a binding or target override, `deploy` opens the project picker.
An unattended invocation fails if selection requires interaction.

## Planning and deployment

`plan` and `deploy` read `uniac.yaml` from the selected project directory.
They select the explicitly named deployment, otherwise `default`, otherwise
the manifest's sole deployment; failure to select a deployment is an error.

A deploy target must contain exactly one entry in `services`. Deployment
performs local planning before any remote action.

Deploying either `image:` or `build:` requires the local Docker daemon.
Prebuilt images are pulled with local Docker credentials. Images target `linux/amd64`.
Builds use the current working tree; the context directory's `.dockerignore`
filters build input, while `.gitignore` does not. Builds run on each
deployment, using Docker's layer cache, with no injected build arguments.
The resulting image is pushed to the project registry.

`UNIAC_STORE_DIR` selects the local release-record directory, which defaults
to `~/.uniac/store`.

With a project name, deployment task ID, and successful initial task read,
the CLI waits for completion or the observation deadline. Without those
conditions, it can return success after registration without observing
completion. Interrupting the CLI does not cancel work already accepted by
the platform.

## Output

`link` writes its listing, prompt, and confirmation to stderr; other
commands' results go to stdout. `UNIAC_PROGRESS=1` enables progress on stderr;
`0` disables it. It does not affect stdout.

`plan --json` emits `{resource, digest, deployable}`, where `deployable` is
the generated service description. Its `env` and `start_command` fields are
included regardless of `--full`; that flag adds them to the text preview only.

`deploy` and `status` emit one final text report and have no JSON output mode.
For these commands, help and argument-parsing errors leave stdout empty.
Message wording and text layout are not a stable parsing interface.

Whole-project `status` reports volumes and their attachment state, including
retained unattached volumes; single-service `status` does not. Whole-project
`status` can omit service details or volumes when additional reads fail,
while still exiting 0.

Reported service state contains no image reference or digest. Allocated
public addresses appear in deployment and status output when the CLI can
read the service's state. [Platform behavior](platform.md) explains what
that state establishes.

## Exit codes

The following codes apply to `deploy` and `status`:

| Exit | Code | Current meaning |
|---|---|---|
| 0 | — | The command succeeded. |
| 2 | `usage` | Invalid invocation; no deployment attempted. |
| 3 | `auth` | No locally usable credential, or `status` has no project name. |
| 4 | `not_linked` | Binding/platform conflict, or deployment's project picker found no projects. |
| 5 | `manifest` | Manifest or deployment-shape error. |
| 6 | `build` | Docker, image-pull, or build failure. |
| 7 | `push` | Image upload failed. |
| 8 | `deploy_failed` | Deployment task failure, observation deadline expiry, or a refused platform read. |
| 9 | `unreachable` | The platform could not be reached. |
| 10 | `pending` | Reserved for unfinished work; currently not emitted. |
| 70 | `internal` | Unclassified error, including unattended project selection failures. |

Exit 1 is unassigned for these two commands. A rejected token can produce
7, 8, or 70 according to the operation. `retryable`, when reported,
indicates whether the same operation may succeed without changes.

For other commands, exit 1 indicates command failure and exit 2 indicates
an invalid invocation.
