# Composition: uniac.yaml

The application description, compressed. Complete contracts:
[Composition in YAML](https://docs.uniac.ai/composition/yaml.md),
[Service](https://docs.uniac.ai/resources/service.md),
[Volume](https://docs.uniac.ai/resources/volume.md).

## File shape

| Top-level field | Required | Meaning |
|---|---|---|
| `resources` | Unless `workspace` is present | Resource name → typed resource. Names match `^[a-z0-9]+(?:(?:__?|-+)[a-z0-9]+)*$` and are unique in the file. |
| `workspace` | No | `name`, `description`, `includes` (literal relative directories, each with its own `uniac.yaml`). |
| `runtime` | No | `yaml`, the only value. |

Every resource needs `type`; unknown fields are rejected at every level.
Three types exist: `service`, `singleton` (both are definitions) and
`deployment` (instantiation).

## Definitions: `type: service` and `type: singleton`

| Field | Required | Meaning |
|---|---|---|
| `image` or `build` | Exactly one | `image: <OCI reference>`, or `build: <dir>` / `build: {root, context, dockerfile, target}`. Paths are relative to the directory holding this `uniac.yaml`; `root` defaults to `.`, `dockerfile` to `Dockerfile`, `target` to the last stage. `image: ""` counts as absent; `build: null` is invalid. |
| `env` | No | Variable name → string value. Names match `^[A-Za-z_][A-Za-z0-9_]*$`; `host` is reserved. Values may hold references (below). |
| `start_command` | No | Replaces the image's `ENTRYPOINT` and `CMD`; split with shell-style quoting and executed directly. |
| `volumes` | No, singleton only | A list of at most one `{name, size_gb, mount_path}` entry. `name` matches `^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$`; `size_gb` is 1–4096, set when the volume is created; `mount_path` is absolute, other than `/`, without `.` or `..` segments or repeated or trailing slashes, outside `/proc`, `/sys` and `/dev`, and other than `/etc/resolv.conf`. |

The definition's name is a local label within its package.

## Instantiation: `type: deployment`

A deployment declaration instantiates one definition as one service, and its
resource name is the service's name: one DNS label (lowercase letters, digits
and dashes, at most 63 characters), unique across the whole project.

| Field | Required | Meaning |
|---|---|---|
| `from` | Yes | A `service` or `singleton` definition in the same file. Several declarations may share one definition. |
| `replicas` | No | An integer, 0–4 for a `service` definition and 0–1 for a `singleton`. Omitted or `null` keeps the service's current count; a new service runs one. |
| `public_ports` | No | List of `{port: 1–65535, type: http \| tcp}`, one of each type at most. Omitted or `null` keeps the service's current exposure on redeploy, `[]` removes it, a list replaces it. |

Every deployment declaration in the project contributes its service, and a
definition runs once a declaration instantiates it. Deploying requires at
least one declaration. Renaming a declaration deploys a new service with its
own hostname, references and volume names; the service under the old name
and its volume stay in the project until they are deleted in the dashboard.

## References inside `env` values

`${{<service>.<VAR>}}` reads a variable the named service declares;
`${{<service>.host}}`, the one builtin, is that service's internal hostname;
`${{self.X}}` reads the declaring service's own value. Chains resolve
transitively. Every `${{` opener must form a valid reference. Service names in
references are local to the package: `uniac plan` rejects a service from
another package or one that does not exist.

Resolution happens when the referencing service's deployment version is
created, against the values the services already serving run with. On a
project's first deploy the siblings are still starting, so their references
are left out, with a warning, until the referencing service's next
deployment.

## Workspaces

A `workspace` document owns its directory tree; each listed `includes` entry
is a **package** with its own `uniac.yaml`, resource names and references.
Paths are literal relative directories below the root; `uniac plan` rejects
globs and nested workspaces and loads exactly the listed manifests.
Root-level `resources` may sit beside `workspace`. The project consists of
the root and its listed packages. Build paths stay relative to the manifest
that declares them, so `build: .` in two packages means two sources.

## A complete composition

An API built from `./api/Dockerfile` listening on 8080, and a private Redis
with durable storage; the API learns Redis's address through a reference.

```yaml
runtime: yaml
resources:
  api_definition:
    type: service
    build: ./api
    env:
      CACHE_URL: "redis://${{cache.host}}:6379"
  cache_definition:
    type: singleton
    image: redis:7-alpine
    start_command: "redis-server --appendonly yes"
    volumes:
      - name: data
        size_gb: 1
        mount_path: /data
  api:
    type: deployment
    from: api_definition
    replicas: 2
    public_ports: [{port: 8080, type: http}]
  cache:
    type: deployment
    from: cache_definition
    public_ports: []
```

`api` runs two replicas and is public over HTTPS; `cache` is reachable only
as `cache.internal`; its volume is `cache.data`. On the project's first
`uniac deploy`, `cache` is still starting when `api`'s version is created, so
`CACHE_URL` is left out; a second `uniac deploy` sets it. `uniac plan --json` shows the generated
description: a `deployable` with one entry per service, `container.source`
as `ref` or `build`, `kind: singleton` and a declared `replicas` where they
apply, and a digest of the normalized description, which formatting, ordering
and default spellings leave unchanged and an explicit build `target` or a
declared `replicas` changes.

## What `uniac plan` catches

Ownership and included manifests, each file's schema and resource names,
`from` lookups, replica counts, unique service names, build paths on disk,
composed volume names, reference targets and variables, and reference cycles,
all checked locally and offline. The platform checks ports, endpoint counts,
env sizes, the `size_gb` range and mount paths when the deployment is
submitted; a singleton deploy compares `size_gb` with the existing volume
after its running replica has stopped.
