# Composition: uniac.yaml

The application description, compressed. Complete contracts:
[Composition in YAML](https://docs.uniac.ai/composition/yaml.md),
[Service](https://docs.uniac.ai/resources/service.md),
[Volume](https://docs.uniac.ai/resources/volume.md).

## File shape

| Top-level field | Required | Meaning |
|---|---|---|
| `resources` | Unless `workspace` is present | Resource name → typed definition. Names match `^[a-z0-9]+(?:(?:__?|-+)[a-z0-9]+)*$` and are unique in the file. |
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
| `start_command` | No | Replaces the image's `ENTRYPOINT` and `CMD`; split with shell-style quoting, no shell involved. |
| `volumes` | No, singleton only | List of `{name, size_gb, mount_path}`; at most one. `name` matches `^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$`; `size_gb` ≥ 1 (platform limit 4096); `mount_path` absolute, not `/`, no `.`/`..`/repeated or trailing slashes, not under `/proc`, `/sys`, `/dev`, not `/etc/resolv.conf`. |

The definition's name is a local label; nothing remote carries it.

## Instantiation: `type: deployment`

| Field | Required | Meaning |
|---|---|---|
| `services` | Yes, nonempty | Instance name → `{from, public_ports}`. The instance name is the remote service's identity: one DNS label, lowercase letters, digits and dashes, at most 63 characters. Names must be unique across the whole project. |
| `services.<name>.from` | Yes | A definition in the same file. Several instances may share one definition. |
| `services.<name>.public_ports` | No | List of `{port: 1–65535, type: http \| tcp}`; at most one of each type. Omitted or `null` keeps the service's current exposure on redeploy, `[]` removes it, a list replaces it. |

Every deployment declaration in the project contributes its instances;
definitions nobody instantiates run nothing. At least one declaration is
required to deploy.

## References inside `env` values

`${{<instance>.<VAR>}}` reads a variable the named service instance declares;
`${{<instance>.host}}` is that service's internal hostname (`host` is the
only builtin); `${{self.X}}` reads the declaring service's own value. Chains
resolve transitively. Every `${{` must be a valid reference — there is no
escape. Instance names in references are local to the package: an instance
from another package, or one that does not exist, fails `uniac plan`.

Resolution happens at deployment. A referenced service that is not yet
serving leaves the variable out, with a warning; it is injected on a later
recreation once that service serves.

## Workspaces

A `workspace` document owns its directory tree; each listed `includes` entry
is a **package** with its own `uniac.yaml`, resource names and references.
Paths are literal directories below the root (no globs, no nesting, no
recursion). Root-level `resources` may sit beside `workspace`. A manifest not
listed is not part of the project. Build paths stay relative to the manifest
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
  api-deployment:
    type: deployment
    services:
      api:
        from: api_definition
        public_ports: [{port: 8080, type: http}]
  cache-deployment:
    type: deployment
    services:
      cache:
        from: cache_definition
        public_ports: []
```

`api` is public over HTTPS; `cache` is reachable only as `cache.internal`;
its volume is `cache.data`. `uniac plan --json` shows the generated
description: a `deployable` with one entry per instance, `container.source`
as `ref` or `build`, `kind: singleton` where applicable, and a digest that
ignores formatting, ordering and default spellings but not an explicit
build `target`.

## What `uniac plan` catches

Ownership and included manifests, each file's schema and resource names,
`from` lookups, unique instance names, build paths on disk, composed volume
names, reference targets and variables, and reference cycles. It does not
touch Docker or the platform; the platform applies its own limits at
submission (ports, endpoint counts, env sizes, volume size, mount paths).
