---
name: uniac
description: "Build, deploy and operate web apps, websites, APIs, databases and background workers on Uniac, the cloud platform for AI agents: containers from Docker images or Dockerfiles, private networking, public HTTP and TCP endpoints, persistent volumes and the uniac CLI. Use when asked to deploy, host or run an application in the cloud, and for any task involving uniac.yaml, the uniac CLI or a project on uniac.ai — describing an application, deploying it, debugging a deployment, or reading a project's state."
---

# Uniac

Uniac is a cloud platform for AI agents to build and deploy web apps,
websites, APIs, databases and background workers. This skill is an expert's
working knowledge of it, compressed for an agent building on it.
Every contract has one authoritative page at https://docs.uniac.ai; this file
and its references summarize them and name the page for each detail. When an
exact field, limit or behavior matters, read the page's Markdown:
`curl -sL https://docs.uniac.ai/<page>.md`. Offline,
`https://docs.uniac.ai/llms-full.txt` is every page in one file.

## The model

- An **account** owns **projects**. A project is a deployment destination with
  its own services, volumes and private network; its name is unique within
  the account and it also has an assigned slug.
- A **service definition** (`type: service` for stateless execution,
  `type: singleton`) holds an image or Dockerfile build, `env`,
  `start_command` and `volumes`. Declaring it runs nothing.
- A **deployment declaration** (`type: deployment`) instantiates definitions
  under **service names**. The name is the service's identity in the project
  and its private hostname, `<name>.internal`.
- **Replicas** are the containers behind that identity. A stateless service
  may run several interchangeable ones; a singleton runs at most one, and a
  replacement stops the old replica before the new one starts.
- A **volume** is durable storage with a project-scoped identity
  (`<service>.<name>`), attachable only to a singleton, one per service. It
  outlives replicas, detachment and service deletion; only explicit volume
  deletion or project deletion destroys its data.
- **Public endpoints** (`public_ports` on the instance) expose the
  application's listen port: `http` becomes an `https://` address on the
  shared edge, `tcp` a public host with an allocated port. Everything else is
  reachable only inside the project.

Platform behavior and limits: [platform.md](references/platform.md).

## The workflow

1. **Describe** the application in `uniac.yaml` at its root
   ([composition.md](references/composition.md)). `uniac init` writes a
   starter for one prebuilt image.
2. **Validate offline** with `uniac plan`: schema, references, build paths.
   No credentials or Docker needed; `--json` prints the generated description.
3. **Sign in once** with `uniac auth login` (browser). In CI, set
   `UNIAC_ACCESS_TOKEN`.
4. **Choose the destination**: `uniac project create <name>`, then
   `uniac link <name-or-slug>`, which writes `.uniac/deploy.json`. Without a
   binding, `deploy` opens a picker and saves the choice.
5. **Deploy** with `uniac deploy`: every image is built or pulled by the local
   Docker daemon for `linux/amd64`, pushed, and every deployment declaration
   submitted; each service is then polled for up to five minutes.
6. **Read state** with `uniac status` (whole project, volumes included) or
   `uniac status <service>`.

Commands, destination selection, output and exit codes:
[operations.md](references/operations.md).

## Decisions

| Question | Answer |
|---|---|
| `service` or `singleton`? | `service` for anything that can run as interchangeable copies: APIs, workers, front ends. `singleton` for anything that must be alone or needs a volume: databases, persistent caches, schedulers. |
| Where does state live? | On a singleton's volume, or outside Uniac. A replica's memory and container files are lost at replacement. |
| Which port? | The application's own listen port, named in `public_ports`. Uniac injects no `PORT` and does not configure the application to match. |
| `http` or `tcp`? | `http` for anything browsers or HTTPS clients call; TLS ends at the edge. `tcp` for raw protocols such as databases; the public port is allocated, not chosen. |
| How do services find each other? | `<service>.internal`, or `${{service.host}}` inside an `env` value. Private traffic needs no port declaration. |
| How does one service learn another's configuration? | `${{other.VAR}}` reads a variable the other service declares; both must be declared in the same package. |
| `build` or `image`? | `build: <dir>` when the Dockerfile lives in the repository; `image: <ref>` for a published image. Exactly one of the two. |
| One file or a workspace? | One `uniac.yaml` for one application. A `workspace` with `includes` when packages in subdirectories each own a `uniac.yaml`; they deploy to one project but cannot reference each other. |

## What goes wrong

- **`deploy` needs a running Docker daemon even for `image:`** — images are
  pulled and pushed locally. Builds target `linux/amd64`; an arm64-only base
  image fails.
- **`.gitignore` does not shape the build**; only `.dockerignore` does. No
  build arguments or build secrets are supplied.
- **The composition sets no replica count** (CLI 0.3.21). Counts are set on
  the platform; after each deploy, check the `replicas` row of `uniac status`
  rather than assuming an earlier scale-up carried over.
- **A singleton replacement has downtime**: the old replica stops before the
  successor starts, and if the successor fails to start the service stays
  down until a working deploy.
- **The platform watches process liveness only.** A hung process counts as
  running; an exited one is restarted. There are no HTTP health or readiness
  probes.
- **References resolve at deploy time.** A reference to a service that is not
  yet serving is omitted from the injected environment with a warning, not an
  error; once that service serves, Uniac recreates the dependents. Nothing
  orders start-up, so applications must retry their connections.
- **Removing a service from `uniac.yaml` does not delete it** — delete it on
  the dashboard. Deleting a service keeps its volume; deleting the project
  destroys every volume, detached ones included.
- **Volumes cannot be resized.** Choose `size_gb` (1–4096) with headroom. The
  same volume name reattaches the same data, even at a new mount path.
- **`public_ports` semantics on redeploy:** omitted keeps the existing
  exposure, `[]` removes it, a list replaces it. At most one `http` and one
  `tcp` endpoint per service.
- **A deploy is not a transaction.** Accepted work continues after a failure
  or an interruption, and there is no rollback command: revert by deploying
  the previous image. Exit 8 after the five-minute window means the work is
  still in progress, not that it failed.
- **Tokens expire and are never refreshed.** `uniac auth status` shows the
  expiry; sign in again. One stored session per platform.
- **`env` values are plaintext**, stored with the deployment and readable
  back; there is no secret store. Keep a file that holds secrets out of
  version control.

## Reading the CLI

`deploy` prints a stage record — `plan`, `link`, `build`, `push <service>`,
`submit <service>`, `observe <service>` — followed by state rows; `status`
prints state. A `service` row carrying `v<N>` means a serving version was
read; a name-only row means the submission was accepted but state was not
read, which does not establish a running service. `endpoint http https://… →
:8080` is the public address and the container port. Exit codes: 2 usage,
3 auth, 4 not linked, 5 manifest, 6 build, 7 push, 8 deployment failed or
observation timed out, 9 platform unreachable.

## A minimal composition

```yaml
runtime: yaml
resources:
  api_definition:
    type: service
    build: .
  main:
    type: deployment
    services:
      api:
        from: api_definition
        public_ports: [{ port: 8080, type: http }]
```

`uniac plan`, `uniac project create my-app`, `uniac link my-app`,
`uniac deploy`, `uniac status` takes this from a directory holding a
`Dockerfile` that listens on port 8080 to a public HTTPS address. A two-service
composition with a database, a volume and environment references is in
[composition.md](references/composition.md#a-complete-composition); the same
walk-through with expected output is the
[quickstart](https://docs.uniac.ai/quickstart.md).
