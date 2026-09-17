# Platform behavior and limits

What Uniac does with a deployed composition, compressed. Complete contracts:
[How Uniac works](https://docs.uniac.ai/index.md),
[Service](https://docs.uniac.ai/resources/service.md),
[Volume](https://docs.uniac.ai/resources/volume.md).

## Services, replicas and versions

- A service instance's identity (name, `<name>.internal`, endpoints, volume)
  persists across replica replacements and deployment versions.
- Each deploy of an instance creates a new **deployment version** of that
  service; the newest successful version serves and older ones retire.
  Redeploying with a different type (`service` ↔ `singleton`) is rejected.
- **Stateless** services run several interchangeable replicas; connections
  may land on any of them. The replica count is not part of the composition
  (CLI 0.3.21); it is set in the dashboard, and `uniac status` reports
  requested, effective and observed counts. Each new deployment version
  starts with one replica, so after a deploy a service that was scaled up, or
  paused at zero, runs one replica.
- **Singleton** services run at most one replica. Replacement stops the old
  replica first, so a version change has a gap; a successor that fails to
  start leaves the service down.
- The platform observes container-process liveness and restarts an exited
  process. It runs no HTTP or readiness probes and offers no dependency
  ordering.
- A `start_command` replaces the image's `ENTRYPOINT` and `CMD`; the image
  itself is unchanged.

## Observed state (`uniac status`)

| Fact | Meaning |
|---|---|
| Serving version `v<N>` | The deployment currently serving. |
| Lifecycle | `preparing`, `active`, `retiring`, `retired`; only non-`active` phases are printed. |
| Replicas | Requested count, effective count after platform policy, observed running count (may be unavailable). |
| Deploying | An in-flight task and its current step. |
| Hold | A platform-side reason the service is not converging. |
| Warning | A non-fatal platform condition, such as an unresolved reference. |

Missing rows mean a read failed or was unavailable, not that the fact is
absent.

## Networking

- Private: every service is `<name>.internal` inside its project, on any
  port the application listens on. No declaration needed.
- Public: `http` gives an `https://<hostname>` address on the shared edge;
  `tcp` gives a public hostname and an allocated port. Both forward to the
  application's declared listen port. At most one endpoint of each type per
  service; ports 1–65535. A `tcp` address stays allocated while the endpoint
  exists.
- Uniac injects no `PORT`; the application chooses its port and the endpoint
  names it.
- Custom domains, per-service TLS certificates and public UDP are not part
  of the interface.

## Environment

- Values are plain strings, up to 64 variables per service, names ≤ 128 and
  values ≤ 4096 characters. Image defaults apply to anything not declared.
- References (`${{other.VAR}}`, `${{other.host}}`, `${{self.VAR}}`) resolve
  once, when the referencing service's deployment version is created, from
  the values the other services' serving versions run with. A reference to a
  service with no serving version — every sibling, on a project's first
  deploy — is omitted with a warning. Nothing re-resolves it later: a service
  picks up another service's new or changed value only in its own next
  deployment version.
- Every `uniac deploy` creates a new version of each declared service, even
  when its configuration is unchanged, so running it again after the
  referenced services serve fills the omitted values. Changing `env` ships a
  new version and restarts the service's replicas.
  Values are stored with the deployment and readable back; there is no
  separate secret store.

## Volumes

| Event | Effect |
|---|---|
| Declaring a new `name` on a singleton | Provisions a fresh volume (containing `lost+found`), named `<service>.<name>`, up to 127 characters. |
| Declaring a name that exists unattached | Reattaches it with its data, even at a different `mount_path`. |
| Declaring a name another service holds | Rejected. |
| Removing the declaration, or deleting the service | Detaches; data is retained as an unattached volume the project still lists. |
| Deleting the volume (dashboard, name confirmation) | Destroys the data; rejected while a service holds it. |
| Deleting the project | Destroys every volume, attached or not. |

`size_gb` is 1–4096 and cannot be changed afterwards. Only singleton
services attach volumes, one each. Whole-project `uniac status` lists volumes
with size and state (`provisioning`, `attaching`, `detaching`, `deleting`,
attached, unattached).

## Projects and the dashboard

- A project keeps live state independently of the description: removing a
  service from `uniac.yaml` leaves it running.
- The dashboard at https://uniac.ai shows projects, services, endpoints,
  volumes and deployment activity, and is where a service or a project is
  deleted (project deletion is confirmed by typing its name) and where
  replica counts are set. It has no application log view and cannot run
  commands in a container.
- Project names match `^[a-z][a-z0-9-]{0,62}$` and are unique per account;
  the platform assigns a slug used in URLs and bindings.
