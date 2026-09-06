# Service

A service runs an application's container image under an instance name in
its project. Its reusable definition supplies the image source and runtime
configuration.

## Definition

`type: service` permits multiple running containers per service;
`type: stateful` limits each service to at most one. Both types share these
fields. Exactly one of `image` or `build` is required; an empty `image: ""`
counts as absent.

| Field | Meaning |
|---|---|
| `image` | OCI image reference. |
| `build` | Dockerfile build source, described below. |
| `env` | Optional mapping of [environment values and references](environment.md). |
| `start_command` | Optional string overriding the image CMD at runtime; the image is unchanged. |
| `volumes` | Optional list of [durable volume declarations](../volume.md). |

[Public endpoints](networking.md) are declared on an instance in a deployment,
independently of the reusable service definition.

The generated description uses `container.source.ref` for `image` and
`container.source.build` for `build`. `type: stateful` adds `kind: stateful`,
while `type: service` omits `kind`.

### Build source

A string `build` value names the build root. An object accepts these optional
fields. An empty string selects the default build root; `build: null` is
invalid.

| Field | Meaning | Default |
|---|---|---|
| `root` | Path relative to the directory containing `uniac.yaml` | `.` |
| `context` | Path relative to the build root | The root itself |
| `dockerfile` | Path relative to the build root | `Dockerfile` |
| `target` | Dockerfile stage name | Last stage |

Paths are relative and checked lexically: `root` must stay within the
directory containing `uniac.yaml`, and `context` and `dockerfile` within the
root. The Dockerfile is located relative to `root`, independently of
`context`.

In the generated description, build paths are normalized and omitted at
their defaults; an all-defaults build is `{}`.

## Runtime and deployment versions

Uniac runs the application's container image without adding an SDK or runtime
dependency to the application.

In live state, a deployment is a version of one service, with its own
lifecycle and running containers. Redeploying an existing instance updates
that service. Redeploying with a different service type is rejected.

The platform observes container-process liveness. It performs no application
health or readiness probes.

## Observed state

| Fact | Meaning |
|---|---|
| Serving version | The service deployment currently serving, identified by its version number. |
| Lifecycle | The deployment's phase: `preparing`, `active`, `retiring`, or `retired`. |
| Requested replicas | The requested container count. |
| Effective replicas | The container count after platform policy is applied. |
| Observed replicas | The running container count reported by the platform; an observation may be unavailable. |
| Deployment task | A deployment operation in flight, with its own state and current step. |
| Hold | A platform-side reason the service is not converging. |
| Warning | A non-fatal condition reported by the platform. |

## Dashboard and removal

A service's dashboard page shows its state, public endpoints, and deployment
activity, and offers **Delete service**. Its volume's retention and deletion
are governed by the [volume lifecycle](../volume.md#lifecycle).
