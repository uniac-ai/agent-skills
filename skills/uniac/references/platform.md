# Running services

A remote project contains services, their public endpoints, and durable
volumes. Each deployed service is identified by its manifest instance name.
Deployments are client-side descriptions; they do not create separate groups
or environments inside a project. A redeploy under the same instance name
updates that service, while another instance name identifies another service.

## Runtime

Uniac runs the application's container image without adding an SDK or runtime
dependency. The image supplies the application and its defaults; the manifest
can override its start command and declare runtime environment variables.
The application controls its own listen port. Uniac does not automatically
supply a `PORT` variable or configure the application to match a public endpoint.

`type: stateful` limits each deployed service to at most one running container,
including zero. `type: service` permits multiple running containers. A service's
type is fixed when first deployed; redeploying the same service with the other type is
rejected. The manifest offers no replica count, scaling, resource-limit, or
placement controls.

## Networking

Services in one project share a private network and are addressable by their
instance names. Internal communication does not require declaring ports in
Uniac; applications use their own protocol and listen-port configuration.
A service without public exposure is reachable only within its project.
Separate environments use separate projects.

The instance's `public_ports` declaration requests public access:

- `http` allocates a hostname on the shared HTTP edge, which routes to the
  application's specified port.
- `tcp` allocates a public hostname and port, forwarding raw TCP to the
  application's specified port. The public port is allocated independently
  of the application's listen port.

The platform accepts ports 1–65535 and at most one exposure of each type per
service. These limits are enforced during deployment, beyond local schema
validation. The allocated addresses appear in deployment and status output
when the CLI can read the service's state. Manifest syntax and the effect of
omitting or replacing exposure are in [manifest.md](manifest.md#public-exposure).

## Environment

The platform resolves declared environment values at deployment time and
injects them at container start. Other environment defaults are the image's
own. `${{...}}` references can read variables and internal hostnames from
other services in the same project, including services deployed separately.

An unresolved reference omits the affected variable from Uniac's injected
values and produces a warning; it does not fail the deployment. After a successful deployment, the
platform re-resolves the project's other services and recreates those whose
injected values changed. Consequently, an independently deployed provider can
supply a previously missing value or cause an existing consumer to restart.
Uniac provides no dependency ordering or readiness coordination.

Environment values are plaintext in the manifest. The manifest has no secrets
management or external-secret reference mechanism; references to another
service's variables use the same environment contract.

## Storage

Only a stateful service can declare durable storage. A volume is a separate
project entity named `<instance>.<local-volume-name>`: instance `database`
with volume `data` uses `database.data`. Another instance name uses a
different volume. The manifest specifies its mount path and size.

Redeploying with the same volume name reuses its data. Removing the volume
declaration on redeploy detaches it; deleting the service also detaches its
volume and preserves its data. Redeploying that service with the same instance
and volume names can adopt the retained volume again. Explicit volume deletion
requires name confirmation and destroys stored data. Volume resizing is
currently unsupported: neither shrinking nor growing an existing volume
is accepted.

A fresh volume contains `lost+found`. Images that require an empty data
directory need a directory below the mount; for PostgreSQL, a mount at
`/var/lib/postgresql/data` can use
`PGDATA=/var/lib/postgresql/data/pgdata`.

## Observation and removal

The platform observes container-process liveness. It performs no application
health or readiness probes, so a running process does not establish that an
HTTP endpoint, database operation, or user flow works. A valid plan likewise
does not establish runtime correctness.

`uniac status` reads current project state, including services no longer
declared in the local manifest. The whole-project view includes volumes and
their attachment state, including volumes retained after service deletion.
`uniac status <service>` reports one service. CLI observation limits, omitted
details, and deployment completion semantics are in [cli.md](cli.md).

Removing a resource from `uniac.yaml` does not delete the deployed service.
The CLI has no removal command. In the [dashboard](https://uniac.ai), signed
in with the project's account, a service's page offers **Delete service**.
The project's **Settings** offers
**Delete project**, confirmed by typing its name; this removes the project's
services and endpoints.
