# Service

A service is a named application component within a project. Each replica
runs a container from an OCI (Open Container Initiative) image, which supplies
the application and its runtime dependencies. The image can be supplied
directly or built from a Dockerfile. Uniac adds no SDK or runtime dependency
to the application.

## Definitions and instances

A **service definition** supplies reusable image and runtime configuration.
A **deployment declaration** instantiates it under a service name in the
target project. A definition alone creates no remote service; deploying a
declaration creates or updates the service instances it names.

A **service instance** is the named remote service; its **replicas** are the
running containers. Its identity persists across replica replacements and
deployment versions.

Stateless services can run multiple container replicas behind the same
service identity; today the platform runs one replica per service, and the
composition does not set the count. A singleton service permits at most one
running replica per service in a project. During replacement, the previous
replica stops before its successor starts. Persistent local storage requires
an attached [volume](volume.md); singleton execution alone does not preserve
data.

## Required and optional configuration

| Information | Required | Meaning |
|---|---|---|
| Execution type | Yes | Stateless or singleton. |
| Container source | Exactly one | An OCI image reference or a Dockerfile build source. |
| Environment variables | No | [Environment values and references](#environment-and-references). |
| Start command | No | Replaces the image's startup command (`ENTRYPOINT` and `CMD`) at runtime; the image is unchanged. |
| Volume attachment | No | [Durable storage](volume.md) for a singleton service. |
| Public exposure | No | [Public endpoints](#public-endpoints) on a service instance. |

A start command is split into arguments with shell-style quoting. A shell is
not automatically invoked.

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

## Networking and endpoints

Services are addressable as `<instance>.internal` within their project.
Internal communication does not require port declarations. Without public
exposure, a service is directly reachable only within its project.

The application chooses its listen port. Uniac does not automatically supply
a `PORT` variable or configure the application to match a public endpoint.

### Public endpoints

A public endpoint forwards incoming traffic to the application's listen port.
Endpoints are declared on the service instance, independently of its reusable
definition.

| Type | Allocated endpoint |
|---|---|
| `http` | An address at `https://<hostname>` on the shared HTTP edge, routing to the application's specified port. |
| `tcp` | A public hostname and port, forwarding raw TCP to the application's specified port. The public port is allocated independently of the listen port. |

Public exposure is optional. Each requested endpoint specifies:

| Field | Required | Meaning |
|---|---|---|
| `port` | Yes | The application's listen port, as a number truncated toward zero. |
| `type` | Yes | `http` or `tcp`. |

The platform accepts ports 1–65535 and at most one exposure of each type per
service. These limits are enforced during deployment, beyond local schema
validation.

## Environment and references

Environment variables provide runtime configuration to a service's containers.
Their values can refer to the service's own configuration or to another
service in the same project. The platform resolves declared values at
deployment time and injects them at container start. Other environment
defaults are the image's own.

Environment configuration is optional. Each declared variable requires a
name and a plaintext string value, optionally containing references. Names
match `^[A-Za-z_][A-Za-z0-9_]*$`; `host` is reserved for the builtin reference.
At deployment, the platform accepts at most 64 declared variables, with names
up to 128 characters and values up to 4096 characters.

### References

A reference's scope names a service instance, independently of its
definition name. `${{self.VAR}}` names a variable on the declaring service.
`host` is the only builtin and means the referenced service's internal
hostname.

References have this grammar:

```text
\$\{\{\s*([a-z0-9][a-z0-9_-]*|self)\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}
```

Chains resolve transitively. Across a chain, `self` remains bound to the
service that declared each value. There is no escape syntax; every `${{`
opener must form a valid reference.

### Resolution

References to `self` must name a builtin or a declared variable. Composition
of a deployment checks references to other instances in that deployment
against their declared variables and builtins, and rejects reference cycles.

A name outside the selected deployment passes through for remote resolution,
even if another deployment in the file defines it. Remote references resolve
within the target project.

Remote references use services with a serving deployment. For those services,
`host` supplies the internal hostname without requiring a running replica;
a custom-variable reference requires that variable in the service's resolved
environment.

An unresolved reference omits the affected variable from Uniac's injected
values and produces a warning; it does not fail the deployment. After a
successful deployment, the platform re-resolves the project's other services
and recreates those whose injected values changed. Uniac provides no
dependency ordering or readiness coordination.

## YAML composition example

In [YAML composition](../composition/yaml.md), `type: service` selects
stateless execution and `type: singleton` selects singleton execution. Exactly
one of `image` or `build` supplies the container source; `image: ""` counts
as absent. Optional configuration uses `env`, the `start_command` string,
and the `volumes` list. `env` maps variable names to string values.

`build` accepts a string naming the build root or an object containing the
build fields above. An empty string selects the default root; `build: null`
is invalid. The application directory is the directory containing
`uniac.yaml`.

`services.<instance>.public_ports` is an optional list of mappings, each with
`port` and `type`. Its presence has three meanings on deployment:

| Value | Result |
|---|---|
| Omitted or `null` | Keeps the service's existing public exposure. |
| `[]` | Removes all public exposure. |
| Nonempty list | Replaces public exposure with exactly this list. |

The `web-code` and `cache-code` resources are definitions. Deploying
`web-deployment` instantiates only `web`; `cache-deployment` instantiates
`cache`. The `from` field connects each instance to its definition.

The stateless `web` service receives the URL declared by `cache`, which uses
`cache`'s own internal hostname. The `web` service's port 8080 is exposed through
HTTPS and a separately allocated raw TCP endpoint. The singleton `cache` service starts
Redis with append-only persistence on a 1 GB volume mounted at `/data`.

```yaml
default: web-deployment
resources:
  web-code:
    type: service
    image: mendhak/http-https-echo:31
    env:
      CACHE_URL: "${{cache.URL}}"
  cache-code:
    type: singleton
    image: redis:7-alpine
    env:
      URL: "redis://${{self.host}}:6379"
    start_command: redis-server --appendonly yes
    volumes:
      - name: data
        size_gb: 1
        mount_path: /data
  web-deployment:
    type: deployment
    services:
      web:
        from: web-code
        public_ports:
          - port: 8080
            type: http
          - port: 8080
            type: tcp
  cache-deployment:
    type: deployment
    services:
      cache:
        from: cache-code
        public_ports: []
```

The generated description uses `container.source.ref` for `image` and
`container.source.build` for `build`. `type: singleton` adds `kind: singleton`,
while `type: service` omits `kind`. Build paths are normalized and omitted at
their defaults; an all-defaults build is `{}`.

## Runtime and deployment versions

In live state, a deployment is a version of one service, with its own
lifecycle and running containers. Redeploying an existing instance updates
that service. Redeploying with a different service type is rejected.

The platform observes container-process liveness. It performs no application
health or readiness probes.

### Observed state

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

### Dashboard and removal

A service's dashboard page shows its state, public endpoints, and deployment
activity, and offers **Delete service**. Its volume's retention and deletion
are governed by the [volume lifecycle](volume.md#lifecycle).
