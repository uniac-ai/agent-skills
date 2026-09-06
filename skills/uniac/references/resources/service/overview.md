# Service

A service is a named application component within a project. It runs
containers from a reusable definition that supplies the image source and
runtime configuration. The service keeps its identity across container
replacements and deployment versions.

Stateless services can run multiple container replicas behind the same
service identity. Stateful services run at most one container and can attach
a [volume](../volume.md) whose data survives container replacement.

## Required and optional configuration

| Information | Required | Meaning |
|---|---|---|
| Execution type | Yes | Stateless or stateful. |
| Container source | Exactly one | An OCI image reference or a Dockerfile build source. |
| Environment variables | No | [Environment values and references](environment.md). |
| Start command | No | Replaces the image's startup command (`ENTRYPOINT` and `CMD`) at runtime; the image is unchanged. |
| Volume attachment | No | [Durable storage](../volume.md) for a stateful service. |

A start command is split into arguments with shell-style quoting. A shell is
not automatically invoked.

[Public endpoints](networking.md) are declared on an instance in a deployment,
independently of the reusable service definition.

### Build source

A build source identifies the source tree, build context, Dockerfile, and
target stage. Each setting has a default:

| Field | Required | Meaning | Default |
|---|---|---|---|
| `root` | No | Path relative to the application directory | `.` |
| `context` | No | Path relative to the build root | The root itself |
| `dockerfile` | No | Path relative to the build root | `Dockerfile` |
| `target` | No | Dockerfile stage name | Last stage |

Paths are relative and checked lexically: `root` must stay within the
application directory, and `context` and `dockerfile` within the root.

## YAML composition example

In [YAML composition](../../composition/yaml.md), `type: service` selects
stateless execution and `type: stateful` selects stateful execution. Exactly
one of `image` or `build` supplies the container source; `image: ""` counts
as absent. Optional configuration uses `env`, the `start_command` string,
and the `volumes` list.

`build` accepts a string naming the build root or an object containing the
build fields above. An empty string selects the default root; `build: null`
is invalid. The application directory is the directory containing
`uniac.yaml`.

The `cache-code` definition starts Redis with append-only persistence. The
deployment instantiates it as `cache` with a 1 GB volume mounted at `/data`.

```yaml
resources:
  cache-code:
    type: stateful
    image: redis:7-alpine
    start_command: redis-server --appendonly yes
    volumes:
      - name: data
        size_gb: 1
        mount_path: /data
  application:
    type: deployment
    services:
      cache:
        from: cache-code
```

The generated description uses `container.source.ref` for `image` and
`container.source.build` for `build`. `type: stateful` adds `kind: stateful`,
while `type: service` omits `kind`. Build paths are normalized and omitted at
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
