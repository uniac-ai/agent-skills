# Uniac CLI

The `uniac` CLI connects a local application composition to a remote project.
Its commands prepare descriptions, deploy services, and read live state.

`npm install -g @uniac/cli` installs the `uniac` command with Node 18+.
`npx -y @uniac/cli …` runs the same command without a global installation.

## Invocation

Local directory options default to the current directory. Flags may appear
before or after a command's positional argument; a surplus argument is a
usage error. `uniac -h` lists commands, and a command's `-h` prints its
usage.

| Invocation | Purpose |
|---|---|
| `uniac init` | Create a starter `uniac.yaml` in the current directory. |
| `uniac plan [--json] [--full] [--dir <path>] [deployment]` | Validate and preview a deployment declaration. |
| `uniac project create <name>` | Create a remote project. |
| `uniac link [-C <path>] [name-or-slug]` | Create or replace a directory's project binding. |
| `uniac deploy [--dir <path>] [deployment]` | Build and deploy the selected declaration. |
| `uniac status [--dir <path>] [service]` | Read a linked project's state, or one named service. |
| `uniac auth <login\|status\|token\|logout>` | Manage [authentication](authentication.md). |
| `uniac version` | Print the installed binary's version, commit and build time. |

`--version` and `-v` are aliases for `version`. The CLI has no removal command.
[Output](output.md) describes result formats, progress and exit codes.

## Local initialization

`init` runs offline and writes one prebuilt-image service definition and a
deployment named `main` that instantiates it. It declares no public exposure.
It prompts for a service name, previews the file and asks for confirmation;
end-of-input accepts the defaults. The default name comes from the directory
name, with `app` as the fallback when it cannot be used. An existing
`uniac.yaml` prevents initialization.

`npm create @uniac@latest` invokes `uniac init` through the `@uniac/create`
package. Initialization creates no remote project or directory binding.

## Project selection

Deployment addresses an existing
[remote project](../overview.md#accounts-projects-and-applications).
`project create <name>` creates one on the authenticated account and prints
its name and assigned slug. It does not prompt or write local files, and
requires neither `uniac.yaml` nor Docker. The name must match
`^[a-z][a-z0-9-]{0,62}$`. Project creation and linking use the
platform selected by `UNIAC_PLATFORM_URL`, whose default and credential
selection are described in [Authentication](authentication.md).

`link` requires a directory containing `uniac.yaml`; it checks that the file
exists without validating its contents. An exact project slug or a uniquely
matching name selects the project without a prompt. No argument opens the
project picker, even when the account has only one project; multiple matching
names also require selection. No match, no projects or unanswered required
input causes failure.

Linking writes or replaces `.uniac/deploy.json` in the selected directory:

| Field | Meaning |
|---|---|
| `project_name` | The remote project's account-scoped name, used for platform reads. |
| `project_slug` | The project's assigned identifier. |
| `gateway_url` | The project gateway used for image uploads and deployment requests. |
| `platform_url` | The platform API origin used for credentials and observations. |

The binding belongs to the local directory. Different directories can select
the same project, and replacing a binding does not move or recreate remote
services.

`deploy` and `status` select their destination as follows:

- A nonempty `UNIAC_PROJECT_URL` supplies a gateway URL or project slug,
  overriding the binding. It supplies no project name, and the platform origin
  comes from `UNIAC_PLATFORM_URL`.
- Otherwise the binding supplies the project gateway and platform. A
  conflicting explicit `UNIAC_PLATFORM_URL` fails before a network call. A
  binding without `platform_url` uses the selected default platform; one
  without `gateway_url` derives the gateway from its slug.
- Without a binding or override, `deploy` opens the project picker and saves
  the selected binding. `status` does not open a picker.

`status` requires a project name from the binding, so a target supplied only
by `UNIAC_PROJECT_URL` cannot support it. Its local directory needs no
`uniac.yaml` or Docker. The command reads services even when they are absent
from the local description; whole-project status also reads volumes.

## Planning and deployment

`plan` and `deploy` read `uniac.yaml` from `--dir`. They select the explicitly
named deployment declaration, otherwise `default`, otherwise the file's sole
deployment. Failure to select a deployment is an error. This selection is
independent of the remote project binding.

`plan` performs [description validation](../composition/yaml.md#validation) offline,
without credentials or Docker. It decodes the whole file and composes the
selected declaration, including checking that its build paths exist. It
does not run Docker builds or check remote project state. `--full` expands the
text preview; `--json` returns the generated description, as specified in
[Output](output.md#plan-output).

`deploy` repeats this planning before authentication or remote activity, then
requires exactly one entry in the selected declaration's `services` mapping.
`plan` accepts declarations with multiple entries; a successful plan does not
establish that this deployment limit is satisfied.

Deployment additionally requires credentials for the target project's
platform and a reachable local Docker daemon for either `image:` or `build:`.
Before Docker or image work, deployment checks the credential with the
platform. For linked or interactively selected projects, it looks up the
slug and requires the returned name, slug and gateway to match the binding.
`UNIAC_PROJECT_URL` instead uses an authenticated account-level project
listing for this check. A saved binding is optional because deployment can
select an existing project interactively.

For [service sources](../resources/service.md#required-and-optional-configuration), deployment pulls
prebuilt images using local Docker credentials or builds from the current
working tree. Both target `linux/amd64`. The build context's `.dockerignore`
filters input; `.gitignore` does not. Builds run on every deployment, use
Docker's layer cache and receive no injected build arguments. The resulting
image is pushed to the project registry and registered with the service
description.

Missing build directories or Dockerfiles fail during local planning.
Dockerfile syntax, missing build stages, failing build commands, image pulls
and daemon availability are checked during image work. The platform applies
the remote [service](../resources/service.md),
[exposure](../resources/service.md#networking-and-endpoints) and
[storage](../resources/volume.md) constraints when the deployment is submitted.

When the target has a project name, registration returns a task ID and the
initial task read succeeds, the CLI polls every two seconds until the task
finishes or a five-minute observation deadline passes. Authentication or
access denial fails the command. Other missing observation conditions can
leave a successful registration unobserved. Interrupting the CLI or reaching
the deadline does not cancel work already accepted by the platform.

After a successful release, the CLI writes a local release record under
`~/.uniac/store`; `UNIAC_STORE_DIR` selects another directory.
[Output](output.md#partial-observations-and-warnings) describes recording
failures.
