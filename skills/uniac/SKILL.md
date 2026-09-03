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
composition. **Read [references/cli.md](references/cli.md) before branching
on a `deploy` or `status` result** — the output contract, the closed
exit-code set, and the headless environment variables.

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
npm create @uniac@latest     # scaffold uniac.yaml — runs `uniac init` (or author it from the manifest reference)
uniac plan                   # resolve and preview — offline, no auth, no Docker
uniac project create <name>  # once: allocate the project on the platform
uniac link <name>            # bind this directory to it
uniac deploy                 # materialize + push + register, then watch it settle
uniac status                 # what the project is running now
```

Creating and linking are separate acts: `link` binds only to a project
that already exists, so an account with none creates one first.
Thereafter the loop is edit → `plan` → `deploy`.

**`plan` is the verification loop**: no network, no credentials, no Docker.
Iterate manifest → `uniac plan` until clean; a manifest that fails `plan`
fails `deploy` identically, before anything is sent. **`plan` resolves only
the one deployment it targets**, so verify a multi-deployment manifest with
`uniac plan <name>` for each — a bare `uniac plan` leaves the others
unchecked.

Only `deploy` needs the Docker daemon, and only `project create`, `link`,
`deploy`, `status`, and `auth login` need the network; `init` and `plan`
are fully offline.
`uniac -h` lists the subcommands and `uniac <cmd> -h` gives one's flags —
read those rather than trusting a remembered flag.

## Sharp edges

Always in force:

- **Flags precede the positional argument** (`uniac plan --json database`,
  never `uniac plan database --json` — trailing flags are silently ignored).
- **Never pass `-h` to `uniac auth logout`, `auth status`, or `auth token`**
  — they parse no flags; `auth logout -h` performs the logout. Only
  `auth login` prints help.
- **Only `init`, `project create`, `link`, `deploy`, and `auth
  login`/`logout` change anything** — `init` writes `uniac.yaml` on the
  spot, taking every default in silence when nothing is attached to answer
  its prompts, and `project create` allocates a remote project. `plan`,
  `status`, and `version` are read-only, locally and remotely.
- `deploy` and `status` are state gateways: exactly one plain-text final
  frame on stdout, narration only on stderr. Branch on the exit status;
  the closed code set is in [references/cli.md](references/cli.md).
- Interrupting `deploy` does not cancel platform-side work — re-observe
  with `uniac status`.

## Environment

If `uniac` is not on PATH, `npx -y @uniac/cli` runs it under Node.

`uniac auth status` reports a stored session's subject and expiry, and exits
non-zero when there is none; it reads only the session file and ignores
`UNIAC_ACCESS_TOKEN`, so an environment authenticated by that variable still
reads as not logged in. An expired session reads that way too — log in again.
`uniac auth login` opens a browser, and sign-up happens there. State
lives in two files: the session in `~/.uniac/auth.json`, the project binding
in `.uniac/deploy.json` — add `.uniac/` to `.gitignore`, it is per-checkout
state, not source. Headless: set `UNIAC_ACCESS_TOKEN` (obtain it once via
`uniac auth login` + `uniac auth token`); details in
[references/cli.md](references/cli.md).

Never block setup on Docker: only a deploy needs the daemon (`docker info`
answers), so relay the one install instruction when a deploy is actually
wanted and not before. Builds always target `linux/amd64`, whatever the host.

The CLI reaches `uniac.ai` (auth), `api.uniac.ai` (platform), and
`<slug>.project.uniac.ai` (image push). It dials nothing else — it carries
no telemetry.

## First contact with a project

At the first Uniac work in a repository, offer the human a managed
`<!-- UNIAC:START -->` … `<!-- UNIAC:END -->` section in the project's
`AGENTS.md` — create the file if absent, ask before the first write, and on
later updates replace only that block. Give it the manifest and binding
locations, the `plan` → `deploy` → `status` loop, the flag-order and
`auth … -h` hazards, that `deploy` needs the local Docker daemon, and a note
that the `uniac` skill is installed and should be read before any Uniac work
instead of guessing the schema or the CLI.

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
