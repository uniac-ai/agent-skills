# Platform behavior

What Uniac does with a deployed composition, compressed. Complete contracts:
[How Uniac works](https://docs.uniac.ai/index.md),
[Service](https://docs.uniac.ai/resources/service.md),
[Volume](https://docs.uniac.ai/resources/volume.md).

## Services, replicas and versions

- A service instance's identity (name, `<name>.internal`, endpoints, volume)
  persists across replica replacements and deployment versions.
- Each deploy of an instance creates a new **deployment version** of that
  service; the newest successful version serves and older ones retire. A
  service keeps its type: a deploy that switches it between `service` and
  `singleton` is rejected.
- **Stateless** services run interchangeable replicas; connections may land on
  any of them. A new deployment version runs the default of one replica; the
  dashboard sets another count, 0–4, and `uniac status` reports requested,
  effective and observed counts. After a deploy, a service that was scaled up,
  or paused at zero, runs one replica until its count is set again.
- **Singleton** services run at most one replica (0 or 1 in the dashboard).
  Replacement stops the old replica first, so each version change has a gap;
  a successor that fails to start leaves the service stopped.
- The platform restarts a container whose process exits; after five
  consecutive restarts that each ran for less than a minute, the container
  stays stopped. Services start independently of one another.

Details: [Runtime and deployment versions](https://docs.uniac.ai/resources/service.md#runtime-and-deployment-versions).
- A `start_command` replaces the image's `ENTRYPOINT` and `CMD`; the image
  itself is unchanged.

## Observed state (`uniac status`)

| Fact | Meaning |
|---|---|
| Serving version `v<N>` | The deployment currently serving. |
| Lifecycle | `preparing`, `active`, `retiring`, `retired`; only non-`active` phases are printed. |
| Replicas | Requested count, effective count after platform policy, observed running count. |
| Deploying | An in-flight task and its current step. |
| Hold | A platform-side reason the service is not converging. |
| Warning | A non-fatal platform condition, such as a reference left out. |

A row missing from a report means that read failed or was unavailable.

## Networking

- Private: every service is `<name>.internal` inside its project, on any port
  the application listens on.
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
| Declaring a name that exists unattached | Reattaches it with its data, even at a different `mount_path`. |
| Declaring a name another service holds | Rejected: a volume has one holder. |
| Removing the declaration, or deleting the service | Detaches; the data stays in an unattached volume the project lists. |
| Deleting the volume (dashboard, name confirmation) | Destroys the data; rejected while a service holds it. |
| Deleting the project | Destroys every volume, attached or unattached. |

`size_gb` is 1–4096, set when the volume is created; later deployments
declare the same size. A singleton service attaches one volume. Whole-project
`uniac status` lists volumes with size and state (`provisioning`,
`attaching`, `detaching`, `deleting`, attached, unattached).

Details: [Volume](https://docs.uniac.ai/resources/volume.md).

## Projects and the dashboard

- A project keeps live state independently of the description: a service
  removed from `uniac.yaml` keeps running until it is deleted.
- The dashboard at https://uniac.ai shows projects, volumes and, per
  service, its state, public endpoints, deployment activity and resource
  usage. It sets replica counts, changes public endpoints, and deletes
  services and projects (project deletion is confirmed by typing its name);
  see [Dashboard and removal](https://docs.uniac.ai/resources/service.md#dashboard-and-removal).
- Project names match `^[a-z][a-z0-9-]{0,62}$` and are unique per account;
  the platform assigns a slug used in URLs and bindings.
