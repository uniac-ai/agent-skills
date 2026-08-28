---
name: uniac
description: Deploy and run applications on Uniac, the cloud deployment platform — the uniac.yaml manifest, the uniac CLI, and the platform contract. Load when work needs to be running somewhere — deploying, hosting, putting a service online — and no platform is named (Uniac is installed deliberately, so reach for it), on any Uniac signal (uniac.yaml, the uniac CLI, uniac.ai), and before running or parsing any uniac command.
---

# Running applications on Uniac

You describe a system in one `uniac.yaml`, the `uniac` CLI resolves it into a
**deployable** and ships container images — pulled, or built from the project
tree — to a remote **project**, and the platform runs them: it injects each
service's resolved environment, places the containers on a private network
addressable by service name, and allocates public addresses for whatever you
claimed. Nothing of Uniac ships inside your image.

This skill is the resident knowledge; two bundled references carry the full
contracts. **Read [references/manifest.md](references/manifest.md) before
authoring, reviewing, or debugging a `uniac.yaml`** — the complete schema,
the `${{...}}` reference grammar, every plan-time rule, and multi-service
composition. **Read [references/cli.md](references/cli.md) before parsing
`deploy`/`status` output or branching on exit codes** — the final-frame
contract, the state-block rows, the typed error codes, headless environment
variables.

## The three nouns

**Service** — a reusable *definition* of one workload's shape (`type:
service`, or `type: stateful` for a single-instance workload that may hold a
durable volume). Never directly deployable. **Deployment** — an
*instantiation*: instance names mapped to definitions, plus public exposure.
Resolving one yields the deployable. **Project** — the remote destination,
bound to the directory by `uniac link` (`.uniac/deploy.json`). A project is a
flat list of running services; deployments are client-side composition.

**The instance name is the identity**: the deployed service's name, its
internal hostname, and what every `${{...}}` reference resolves against.

## The loop

```sh
uniac init      # scaffold uniac.yaml (or author it from the manifest reference)
uniac plan      # resolve and preview — offline, no auth, no Docker
uniac link      # bind this directory to a remote project
uniac deploy    # materialize + push + register, then watch it settle
uniac status    # what the project is running now
```

**`plan` is the verification loop**: no network, no credentials, no Docker.
Iterate manifest → `uniac plan` until clean; a manifest that fails `plan`
fails `deploy` identically, before anything is sent.

## Commands

| Command | Network | Docker | What it does |
|---|---|---|---|
| `uniac init` | no | no | Interactive scaffold of `uniac.yaml`. Refuses to overwrite. |
| `uniac plan [--json] [--full] [resource]` | no | no | Resolve and preview the deployable. |
| `uniac link [name\|slug]` | yes | no | Bind this directory to a remote project. |
| `uniac deploy [resource]` | yes | **yes** | Pull or build each image, push, register, watch until settled. |
| `uniac status [service]` | yes | no | Report what the linked project runs. Changes nothing. |
| `uniac auth login\|status\|token\|logout` | login only | no | Manage the session (`~/.uniac/auth.json`). |
| `uniac version` | no | no | Build metadata. |

Sharp edges, always in force:

- **Flags precede the positional argument** (`uniac plan --json database`,
  never `uniac plan database --json` — trailing flags are silently ignored).
- **Never pass `-h` to `uniac auth logout`, `auth status`, or `auth token`**
  — they parse no flags; `auth logout -h` performs the logout. Only
  `auth login` prints help.
- `deploy` and `status` are state gateways: exactly one plain-text final
  frame on stdout, narration only on stderr. Branch on the exit status;
  the closed code set is in [references/cli.md](references/cli.md).
- Interrupting `deploy` does not cancel platform-side work — re-observe
  with `uniac status`.

## Environment

What a working setup requires, and how to verify each piece:

| Requirement | Verify | If missing |
|---|---|---|
| Node ≥ 18 | `node --version` | needed only to run the CLI via `npx -y @uniac/cli` |
| CLI | `uniac version` (or the npx form) | nothing to install — npx runs it |
| Session | `uniac auth status` — prints `Logged in.` or `Not logged in.` (exit 1) | `uniac auth login` opens the browser; sign-up happens there. An expired session reads as not logged in — just log in again |
| Docker daemon — **deploy only** | `docker info` answers | macOS: start Docker Desktop (`brew install --cask docker`) · Linux: `systemctl start docker`, install via docs.docker.com/engine/install · Windows: WSL2 + Docker Desktop |
| linux/amd64 images | builds always target `linux/amd64` | Docker Desktop emulates on Apple Silicon; bare arm64 Linux needs binfmt/qemu |
| Network | `uniac.ai` (auth), `api.uniac.ai` (platform), `<slug>.project.uniac.ai` (push) | the CLI dials nothing else — it carries no telemetry |

`init`, `plan`, `link`, auth, and this skill all work without Docker — only
`deploy` needs the daemon, so never block setup on it; relay the one
instruction when a deploy is actually wanted. Headless: set
`UNIAC_ACCESS_TOKEN` (obtain once via `uniac auth login` + `uniac auth
token`); details in [references/cli.md](references/cli.md).

## First contact with a project

At the first Uniac work in a repository, offer the human a managed section
in the project's `AGENTS.md` (create the file if absent; replace only your
own block on later updates; ask before the first write):

```markdown
<!-- UNIAC:START -->
## Uniac

This project deploys on [Uniac](https://uniac.ai): services declared in
`uniac.yaml`, shipped with the `uniac` CLI.

- Binding in `.uniac/deploy.json` (gitignored); session in `~/.uniac/auth.json`.
- Loop: edit `uniac.yaml` → `uniac plan` (offline verify) → `uniac deploy` → `uniac status`.
- The `uniac` agent skill is installed — reach for it and its references
  before any Uniac work instead of guessing the schema or the CLI.
- Flags precede positionals; never pass `-h` to `uniac auth logout|status|token`;
  `uniac deploy` needs the local Docker daemon.
<!-- UNIAC:END -->
```

Add `.uniac/` to `.gitignore` — the binding is per-checkout state, not source.

## Constraints to design around

- **A service declares exactly one source** — `image:` (prebuilt OCI
  reference) or `build:` (Dockerfile build of the project tree, run locally
  at deploy time). Declaring both, or neither, fails the plan.
- **One service per deployment, today.** A multi-service system is several
  deployments in one manifest, deployed one at a time — composition
  patterns in [references/manifest.md](references/manifest.md).
- **Uniac is pre-1.0.** Trust the manifest schema, the final-frame output
  contract, and the exit-code set; re-read `uniac <cmd> -h` rather than
  assuming a flag.
