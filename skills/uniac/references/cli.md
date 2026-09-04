# CLI

`uniac …` can run as `npx -y @uniac/cli …` with Node ≥ 18, or through a
global installation from `npm i -g @uniac/cli`.

For commands accepting positional arguments, flags precede them:
`uniac plan --json database`. Parsing stops at the first positional argument;
trailing flags are ignored.
`uniac -h` lists commands and `uniac <command> -h` lists flags.

## Commands

| Command | Effect and requirements |
|---|---|
| `init` | Writes a starter `uniac.yaml` with one prebuilt-image service and its deployment. Offline; takes defaults when unattended. `npm create @uniac@latest` invokes it. |
| `plan [deployment]` | Validates and resolves a manifest locally. No credentials, network, or Docker; validation limits are in [manifest.md](manifest.md). |
| `project create <name>` | Creates a remote project. Requires authentication and network access. |
| `link [name-or-slug]` | Creates or replaces the binding between a directory containing `uniac.yaml` and an existing project. Requires authentication and network access; omitting the argument opens a project picker. |
| `deploy [deployment]` | Builds or pulls an image, uploads it, and requests deployment. Requires a project target, credentials, network access, and Docker. Can also write a directory binding through its project picker. |
| `status [service]` | Reads remote state for a linked project or one service. Requires credentials and network access. |
| `auth login` | Starts browser sign-in and stores the resulting session. Reports whether the browser opened and prints the sign-in URL. Requires network access and the user's browser interaction. |
| `auth status` | Reads stored sessions and their expiry locally. Does not validate credentials or inspect `UNIAC_ACCESS_TOKEN`. |
| `auth token` | Prints the current token from the environment override or the selected platform's stored session. |
| `auth logout` | Removes all stored platform sessions. |
| `version` | Prints the installed version. |

## Authentication and project selection

Sessions are stored per platform in `~/.uniac/auth.json`. An expired stored
token requires another login; `UNIAC_ACCESS_TOKEN` overrides stored tokens.

`link` writes `.uniac/deploy.json`, containing
`{project_slug, project_name, gateway_url, platform_url}`. This records the
checkout's destination and is not project source. `deploy` and `status` use
its recorded platform; a conflicting `UNIAC_PLATFORM_URL` fails before a
network call.

Without a binding or target override, `deploy` opens the project picker.
An unattended invocation fails if selection requires interaction.
`UNIAC_ACCESS_TOKEN` and `UNIAC_PROJECT_URL` together permit deployment
without a browser or picker.

**`UNIAC_PROJECT_URL` overrides the binding but supports deployment only.**
It supplies no project name for observation, so `status` with this variable
set fails with exit 3 even in a linked directory. `status` requires a binding
and the variable unset.

| Variable | Meaning |
|---|---|
| `UNIAC_ACCESS_TOKEN` | Access token for the selected platform. |
| `UNIAC_PROJECT_URL` | Deployment target as a gateway URL or project slug; takes precedence over the directory binding. |
| `UNIAC_PLATFORM_URL` | Platform API origin for login, `auth token`, project creation, linking, and target overrides. Default: `https://api.uniac.ai`. |
| `UNIAC_AUTH_HOST` | Browser sign-in host. Defaults to `uniac.ai` for the default platform; required for another platform unless login's `--host` is supplied. |
| `UNIAC_PROGRESS` | `1` enables progress on stderr; `0` disables it. Does not affect stdout. |
| `UNIAC_STORE_DIR` | Local release-record directory. Default: `~/.uniac/store`. |

## Deployment

Both `image:` and `build:` require the local Docker daemon. Prebuilt images
are pulled with local Docker credentials; builds use the declared Dockerfile
and context. Images target `linux/amd64`. Builds run on each deployment,
using Docker's layer cache, with no injected build arguments. The resulting
image is pushed to the project registry.

When a project name and deployment task ID are available, the CLI waits for
the task to finish. Without either, or if the first task read fails, it can
return success after registration without observing completion. This includes
deployment through `UNIAC_PROJECT_URL`. Interrupting the CLI does not cancel
work already accepted by the platform.

## Output and exit codes

`plan --json` emits the [generated artifact](manifest.md#planning-and-the-generated-artifact).
Its `env` and `start_command` fields are included regardless of `--full`;
that flag adds them to the text preview only.

`deploy` and `status` emit one final text report on stdout; progress goes to
stderr. They have no JSON output mode. Help and argument-parsing errors leave
stdout empty. Exit status and error codes carry command outcomes; message
wording and text layout are not a parsing interface. A project label in a
deploy report can appear even when the failure happened locally.

The following codes apply to `deploy` and `status`:

| Exit | Code | Current meaning |
|---|---|---|
| 0 | — | The command succeeded. Deployment observation can be incomplete as described above; a successful status read does not establish application health. |
| 2 | `usage` | Invalid invocation; no deployment attempted. |
| 3 | `auth` | No usable credential, or `status` has no project name, including with `UNIAC_PROJECT_URL`. |
| 4 | `not_linked` | Binding/platform conflict, or deployment's project picker found no projects. |
| 5 | `manifest` | Manifest or deployment-shape error, including more than one service in the selected deployment. |
| 6 | `build` | Docker, image-pull, or build failure. |
| 7 | `push` | Image upload failed. |
| 8 | `deploy_failed` | Deployment task failure, observation deadline expiry, or a refused platform read. For `status`, this describes the read, not workload health. |
| 9 | `unreachable` | The platform could not be reached. |
| 10 | `pending` | Reserved for unfinished work; currently not emitted. |
| 70 | `internal` | Unclassified error, including unattended project selection failures. Does not by itself establish a CLI defect. |

Exit 1 is unassigned for these two commands. A rejected token can produce
7, 8, or 70 according to the operation; exit 3 does not cover all credential
failures. `retryable`, when reported, indicates whether the same operation
may succeed without changes.

Whole-project `status` can omit service details or volumes when those
additional reads fail, while still exiting 0. A direct `status <service>`
read failure instead fails the command. Only whole-project `status` reports
volumes. Reports contain current service state, not image references or
digests. [Platform behavior](platform.md) explains what that state establishes.

Other commands generally return 1 on failure and 2 on usage errors.
`link` writes its listing, prompt, and confirmation to stderr; other
commands' results go to stdout.
