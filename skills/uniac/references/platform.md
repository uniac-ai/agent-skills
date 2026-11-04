# Platform behavior

What Uniac does with a deployed composition, compressed. Complete contracts:
[How Uniac works](https://docs.uniac.ai/index.md),
[Service](https://docs.uniac.ai/resources/service.md),
[Volume](https://docs.uniac.ai/resources/volume.md).

## Services, replicas and versions

- A service's identity (name, endpoints, volume) persists
  across replica replacements and deployment versions.
- Each deploy of a declaration creates a new **deployment version** of its
  service; the newest successful version serves and older ones retire. A
  deploy succeeds once the new version's containers are started and the
  older versions' containers are removed, `replicas: 0` included; a container
  that exits after starting does not fail it, and one that cannot start
  does. A
  service keeps its type: a deploy that switches it between `service` and
  `singleton` is rejected.
- **Stateless** services run interchangeable replicas; connections may land on
  any of them. The declaration's `replicas` (0–4) sets the count on each
  deploy; without it, a new version keeps the service's count, set in the
  dashboard or by an earlier deploy, including zero, and a new service starts
  with one replica. `uniac status` reports requested, effective and observed
  counts.
- **Singleton** services run at most one replica: `replicas` and the
  dashboard accept 0 or 1.
  Replacement stops the old replica first, so each version change has a gap;
  a successor that fails to start leaves the service stopped.
- Each replica runs as an **instance**, `healthy` while its container's
  process runs; it receives new connections only while `healthy`, and
  connections before the application listens are refused. The platform
  restarts a container whose process exits (`unhealthy` meanwhile); after
  five consecutive restarts that each ran for less than a minute, the
  container stays stopped (`failed`). Services start independently of one
  another.
- An instance's **key** is a UUID it keeps for its life, across a move to
  another node; a new version, a size change, a scale-up and the replacement
  of a `failed` instance start instances with new keys.
- **Logs** are kept with an instance's placement on its node: what it writes
  to stdout and stderr, for its current run and the run before it (a run is
  one container start), each run's last 8 MiB, across restarts and while
  `failed`. They go with the instance when a deploy replaces its version, a
  scale-down, pause or delete removes it, or the platform replaces it after
  it failed; a move starts its runs over. An instance whose container never
  started has none.
- An **exec** runs one command to completion in a running instance's
  container, as the container's own process: the image's user, the
  instance's environment and working directory, its hardening and limits (a
  command's memory counts against the instance's), with no shell added and
  no terminal. A command is 1 to 256 strings (64 KiB together), stdin at
  most 1 MiB, the timeout 1–300 s (default 60); output past 16 MiB across
  both streams is counted, not sent. At the timeout or a disconnect the
  command gets SIGTERM, then SIGKILL 5 s later; processes it leaves in the
  background keep running. An account holds 4 open execs and an instance 2.
  An instance that is not running refuses it with its state. Each exec runs
  the command again, and a refusal that the platform cannot run it now can
  follow a command that started and was stopped. Execs are recorded (who,
  which command, how it ended), their output is not.
- A `start_command` replaces the image's `ENTRYPOINT` and `CMD`; the image
  itself is unchanged.

Details: [Runtime and deployment versions](https://docs.uniac.ai/resources/service.md#runtime-and-deployment-versions),
[Instances](https://docs.uniac.ai/resources/service.md#instances),
[Logs](https://docs.uniac.ai/resources/service.md#logs),
[Exec](https://docs.uniac.ai/resources/service.md#exec).

## Size

- `memory_mib` is a hard limit for a container's processes together: past
  it, a process is OOM-killed. `vcpu` is a ceiling on shared CPU.
- A size belongs to a version: a deploy that omits a value keeps the
  serving version's, and a new service gets 1 vCPU and 512 MiB. A version
  from before sizing, at 256 MiB, moves to 512 MiB when a deploy omits
  `memory_mib`.
- Each replica's memory is reserved on its node. A replica no node has room
  for stays `starting`, and its deploy stays in progress until a node has
  room. Deleting the service always ends the wait; a lower replica count set
  in the dashboard replaces a waiting change to the serving version's count;
  a new singleton deploy replaces it; a new stateless deploy replaces it
  only once running, so it must fit beside the serving version and the
  waiting version's placed replicas. A stateless deploy needs room for the
  new version beside the old; a singleton's old replica stops first, so it
  can stay stopped until room appears, even at the same size.

Details: [Size](https://docs.uniac.ai/resources/service.md#size).

## Observed state (`uniac status`)

| Fact | Meaning |
|---|---|
| Serving version `v<N>` | The deployment currently serving. |
| Lifecycle | `preparing`, `active`, `retiring`, `retired`; only non-`active` phases are printed. |
| Size | The serving version's vCPUs and memory in MiB. |
| Replicas | Requested count, effective count after platform policy, observed count of `healthy` or `unhealthy` instances (unreported while a replica cannot be observed). |
| Instances | Each instance's status — `starting`, `healthy`, `unhealthy`, `failed`, `terminating`, `unknown` — and start time, a previous version's included while it stops. |
| Deploying | An in-flight task and its current step. |
| Hold | A platform-side reason the service is not converging. |
| Warning | A non-fatal platform condition, such as a reference left out. |

A missing row leaves that fact unknown: reports leave out rows they could
not read, `lifecycle` when it is `active`, and `replicas` when the requested
and effective counts match.

## Networking

- Private: inside its project, every service is reached at its name, on any
  port the application listens on.
- Public: `http` gives an `https://<hostname>` address that Uniac issues on the
  shared edge, and a request times out after 60 seconds. `tcp` gives a
  Uniac-issued public hostname and an allocated port, which stays allocated
  while the endpoint exists. Both forward to the application's declared
  listen port. Each service has one endpoint of each type at most, on ports
  1–65535.
- The application chooses its listen port and the endpoint names it; an
  application that reads `PORT` gets it from a declared `env` value.

Details: [Networking and endpoints](https://docs.uniac.ai/resources/service.md#networking-and-endpoints).

## Environment

- Values are strings: up to 64 variables per service, names up to 128 and
  values up to 4096 characters. Undeclared variables keep the image's
  defaults.
- References (`${{other.VAR}}`, `${{other.host}}`, `${{self.VAR}}`) resolve
  when the referencing service's deployment version is created, against the
  values the services already serving run with, and stay with that version.
  On a project's first deploy the siblings are still starting, so their
  references are left out with a warning. A service picks up another
  service's new or changed value in its own next deployment version.
- Every `uniac deploy` creates a new version of each declared service, so
  running it again after the referenced services serve fills the left-out
  values. Changing `env` ships a new version and restarts the service's
  replicas.
- Values are stored with the deployment, and the dashboard shows the serving
  version's values.

Details: [Environment and references](https://docs.uniac.ai/resources/service.md#environment-and-references),
[Resolution](https://docs.uniac.ai/resources/service.md#resolution).

## Volumes

| Event | Effect |
|---|---|
| Declaring a new `name` on a singleton | Provisions a fresh volume (containing `lost+found`), named `<service>.<name>`, up to 127 characters. |
| Declaring a name no service is bound to | Binds it with its data, even at a different `mount_path`. |
| Declaring a name another service is bound to | Rejected: a volume is bound to one service at a time. |
| Declaring a volume being deleted | Rejected when the deploy is submitted. |
| Declaring an existing volume with a larger `size_gb` | Grows it: the deploy completes without waiting, and the running container sees the space within seconds, without a restart. |
| Declaring an existing volume with a smaller `size_gb` | Accepted; the volume keeps its size, since a volume never shrinks. |
| Removing the declaration, or deleting the service | Unbinds it; the data stays in the volume, which the project lists as `available` once its storage is released. |
| Deleting the volume (dashboard, name confirmation) | Destroys the data; the volume is gone once its storage is released. Rejected while a service is bound to it. |
| Deleting the project | Destroys every volume, bound or not. |

`size_gb` is 1–4096 GiB. A growth is pending until the storage has grown: the
volume's requested size is above its size, and it is retried; a deploy that
declares the current size or less withdraws it. A volume still being created takes
the latest declared size. Storage is charged at the volume's size, the grown
size from the minute the volume shows it. A singleton service is bound to at
most one volume.
Whole-project `uniac status` lists volumes with size and state (`bound`,
`available`, `provisioning`, `releasing`, `deleting`).

Details: [Volume](https://docs.uniac.ai/resources/volume.md),
[Lifecycle](https://docs.uniac.ai/resources/volume.md#lifecycle),
[States](https://docs.uniac.ai/resources/volume.md#states).

## Projects and the dashboard

- A project keeps live state independently of the description: a service
  removed from `uniac.yaml` keeps running until it is deleted.
- The dashboard at https://uniac.ai shows projects, volumes and, per
  service, its state, public endpoints, deployment activity and resource
  usage. It sets replica counts, changes public endpoints, and deletes
  services, volumes and projects, each confirmed by typing its name; the CLI
  deletes services and volumes too. Deleting a service reports `terminating`
  until removal completes;
  see [Dashboard and removal](https://docs.uniac.ai/resources/service.md#dashboard-and-removal).
- Project names match `^[a-z][a-z0-9-]{0,62}$` and are unique per account;
  the platform assigns a slug used in URLs and bindings.
