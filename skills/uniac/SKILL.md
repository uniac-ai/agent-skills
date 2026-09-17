---
name: uniac
description: Build, deploy and operate applications on Uniac, a cloud platform that runs OCI containers as connected services with private networking, public endpoints and durable volumes. Use for any task involving uniac.yaml, the uniac CLI or a project on uniac.ai — describing an application, deploying it, debugging a deployment, or reading a project's state.
---

# Uniac

An expert's working knowledge of Uniac, compressed for an agent building on it.
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
  `start_command` and `volumes`. A definition runs once a deployment
  declaration instantiates it.
- A **deployment declaration** (`type: deployment`) instantiates definitions
  under **service names**. The name is the service's identity in the project
  and its private hostname, `<name>.internal`.
- **Replicas** are the containers behind that identity. A stateless service
  runs several interchangeable ones; a singleton runs at most one, and a
  replacement stops the old replica before the new one starts.
- A **volume** is durable storage with a project-scoped identity
  (`<service>.<name>`), held by one singleton service at a time. Its data
  outlives replicas, detachment and service deletion; deleting the volume or
  the project destroys it.
- **Public endpoints** (`public_ports` on the instance) expose the
  application's listen port: `http` becomes an `https://` address on the
  shared edge, `tcp` a public host with an allocated port. Services reach one
  another privately inside the project.

Platform behavior: [platform.md](references/platform.md).

## The workflow

1. **Describe** the application in `uniac.yaml` at its root
   ([composition.md](references/composition.md)). `uniac init` writes a
   starter for one prebuilt image.
2. **Validate** with `uniac plan`: schema, references and build paths, checked
   locally and offline; `--json` prints the generated description.
3. **Sign in once** with `uniac auth login` (browser). In CI, set
   `UNIAC_ACCESS_TOKEN`.
4. **Choose the destination**: `uniac project create <name>`, then
   `uniac link <name-or-slug>`, which writes `.uniac/deploy.json`. Without a
   binding, `deploy` opens a picker and saves the choice.
5. **Deploy** with `uniac deploy`: every image is built or pulled by the local
   Docker daemon for `linux/amd64`, pushed, and every deployment declaration
   submitted as a new version of its service, which replaces the service's
   replicas; each service is then polled for up to five minutes.
6. **Read state** with `uniac status` (whole project, volumes included) or
   `uniac status <service>`.

Commands, destination selection, output and exit codes:
[operations.md](references/operations.md).

## Decisions

| Question | Answer |
|---|---|
| `service` or `singleton`? | `service` for anything that can run as interchangeable copies: APIs, workers, front ends. `singleton` for anything that must be alone or needs a volume: databases, persistent caches, schedulers. |
| Where does state live? | On a singleton's volume, or in an external store. A replica's memory and container files last as long as the replica. |
| Which port? | The application's own listen port, named in `public_ports`. An application that reads `PORT` gets it from a declared `env` value. |
| `http` or `tcp`? | `http` for anything browsers or HTTPS clients call; TLS ends at the edge, and a request has 60 seconds. `tcp` for raw protocols such as databases; Uniac allocates the public port. |
| How do services find each other? | `<service>.internal`, or `${{service.host}}` inside an `env` value, on any port the application listens on. |
| How does one service learn another's configuration? | `${{other.VAR}}` reads a variable the other service declares in the same package. |
| `build` or `image`? | `build: <dir>` when the Dockerfile lives in the repository; `image: <ref>` for a published image. Exactly one of the two. |
| One file or a workspace? | One `uniac.yaml` for one application. A `workspace` with `includes` when packages in subdirectories each own a `uniac.yaml`; they deploy to one project, and each package's references stay within it. |

## Behaviors to plan for

- **Deploys use the local Docker daemon.** `uniac deploy` builds or pulls
  every image locally, `image:` sources included, for `linux/amd64`, and
  pushes it; base images need an amd64 variant. `.dockerignore` shapes the
  build context.
- **Each deploy starts every service at one replica.** Every declared service
  gets a new version, and a new version starts with one replica: a service
  scaled up, or paused at zero, in the dashboard runs one replica after
  `uniac deploy` until its count is set again.
- **A singleton's replacement stops the old replica first.** Each deploy of a
  singleton has a gap, and a successor that fails to start leaves the service
  stopped until a working deploy.
- **The platform restarts a container whose process exits**, and reports the
  service running while its process runs. After five consecutive restarts
  that each ran for less than a minute, the container stays stopped.
- **References resolve when a service's version is created**, against the
  services serving at that moment. On a project's first deploy, references to
  services deployed in the same run are left out with a warning, and a second
  `uniac deploy` fills them in; a changed value reaches another service in
  that service's next deployment. Services start independently, so
  applications retry their connections to one another.
- **A service stays until it is deleted in the dashboard.** Removing it from
  `uniac.yaml` leaves it running. Deleting a service keeps its volume;
  deleting the project destroys every volume, detached ones included.
- **`size_gb` (1–4096) is set when a volume is created**, and later
  deployments declare the same size, so choose it with headroom. The same
  volume name reattaches the same data, even at a new mount path.
- **`public_ports` on redeploy:** omitted keeps the existing exposure,
  including endpoints changed in the dashboard; `[]` removes it; a list
  replaces it. Each service has one `http` and one `tcp` endpoint at most.
- **Each service's submission proceeds on its own.** Accepted work continues
  after a local failure or an interruption; to return to an earlier release,
  deploy its image again. Exit 8 after the five-minute window means the work
  is still in progress.
- **Tokens expire.** `uniac auth status` shows when; `uniac auth login` stores
  a new one, one session per platform.
- **`env` values are stored with the deployment** and shown in the dashboard;
  keep a `uniac.yaml` that carries secret values out of version control.

Contracts: [runtime and versions](https://docs.uniac.ai/resources/service.md#runtime-and-deployment-versions),
[resolution](https://docs.uniac.ai/resources/service.md#resolution), [public endpoints](https://docs.uniac.ai/resources/service.md#public-endpoints),
[dashboard and removal](https://docs.uniac.ai/resources/service.md#dashboard-and-removal),
[volume](https://docs.uniac.ai/resources/volume.md).

## Reading the CLI

`deploy` prints a stage record — `plan`, `link`, `build`, `push <service>`,
`submit <service>`, `observe <service>` — followed by state rows; `status`
prints state. A `service` row carrying `v<N>` means a serving version was
read; a name-only row means the submission was accepted, and `uniac status`
reads the service's state. `endpoint http https://… → :8080` is the public
address and the container port. Exit codes: 2 usage, 3 auth, 4 not linked,
5 manifest, 6 build, 7 push, 8 deployment failed or observation timed out,
9 platform unreachable.

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
