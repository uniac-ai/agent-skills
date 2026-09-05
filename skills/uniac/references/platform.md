# Running services

In live state, a deployment is a version of one service, with its own
lifecycle and running containers. Redeploying an existing instance updates
that service. Applying a deployment does not remove services absent from
the manifest.

## Runtime

Uniac runs the application's container image without adding an SDK or runtime
dependency.

`type: stateful` limits each service to at most one running container.
`type: service` permits multiple running containers. Redeploying a service
with a different type is rejected.

## Networking

Services are addressable by their instance names within the project.
Internal communication does not require port declarations. Without public
exposure, a service is directly reachable only within its project.
Uniac does not automatically supply a `PORT` variable or configure the
application to match a public endpoint.

Public endpoint allocation:

- `http` allocates a hostname on the shared HTTP edge, which routes to the
  application's specified port.
- `tcp` allocates a public hostname and port, forwarding raw TCP to the
  application's specified port. The public port is allocated independently
  of the application's listen port.

The platform accepts ports 1–65535 and at most one exposure of each type per
service. These limits are enforced during deployment, beyond local schema
validation.

## Environment

The platform resolves declared environment values at deployment time and
injects them at container start. Other environment defaults are the image's
own. Remote environment references resolve within the target project.

An unresolved reference omits the affected variable from Uniac's injected
values and produces a warning; it does not fail the deployment. After a
successful deployment, the platform re-resolves the project's other services
and recreates those whose injected values changed.
Uniac provides no dependency ordering or readiness coordination.

## Storage

Redeploying with the same volume name reuses its data. Removing the volume
declaration on redeploy detaches it; deleting the service also detaches its
volume and preserves its data. Existing volumes cannot be resized.

A fresh volume contains `lost+found`.

## Observation and removal

The platform observes container-process liveness. It performs no application
health or readiness probes.

The [dashboard](https://uniac.ai) reads projects directly, with no local
manifest or directory binding. Signed in with the project's account,
**Projects** opens the project's services; selecting a service shows its
state, public endpoints, and deployment activity.

A service's dashboard page offers **Delete service**.
Explicit volume deletion requires name confirmation and destroys stored data.
The project's **Settings** offers **Delete project**, confirmed by typing its
name; this removes the project's services and endpoints.
