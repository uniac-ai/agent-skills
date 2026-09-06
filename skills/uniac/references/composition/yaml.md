# Composition in YAML

`uniac.yaml` is the entrypoint for an application composition. It describes
one or more named resources in YAML: reusable service definitions and the
deployment declarations that instantiate them. YAML is the currently
supported composition format.

## File format

The document is a mapping with these top-level fields:

| Field | Required | Meaning |
|---|---|---|
| `resources` | Yes | Nonempty mapping of resource names to typed definitions. |
| `runtime` | No | Composition format: `yaml`, the default and only supported value. |
| `default` | No | Deployment resource selected when no target is named explicitly. |

Resource names match `^[a-z0-9]+(?:(?:__?|-+)[a-z0-9]+)*$` and are unique
within the file. Every resource requires `type`; unknown fields are rejected
at every level.

## Definitions and service instances

`type: service` and `type: singleton` create reusable **service definitions**
for stateless and singleton execution. A definition holds the OCI image or
Dockerfile build source, environment, startup command, and storage needs.
Declaring it alone creates no remote service. Complete field contracts are
in [Service](../resources/service.md) and [Volume](../resources/volume.md).

A `type: deployment` resource **instantiates** definitions: its `services`
mapping gives each instance a service name and a definition to instantiate.
The selected declaration contributes its named instances to the deployment
description; unreferenced definitions and other deployment declarations in
the file are not included.

| Field | Required | Meaning |
|---|---|---|
| `services` | Yes | Nonempty mapping of instance names to definitions and public exposure. |
| `services.<instance>.from` | Yes | Name of a `service` or `singleton` definition in this file. |
| `services.<instance>.public_ports` | No | [Public endpoint declarations](../resources/service.md#public-endpoints). |

The **service instance** is the named remote service, not an individual
container replica. Multiple instances can reuse one definition. The
definition's name is a local label; the instance name supplies the service's
identity in the target project. An instance name is one DNS label: lowercase
letters, digits and dashes, starting and ending with a letter or digit, at
most 63 characters.

Only a deployment declaration is a selectable target. It creates no remote
service group or environment; each resulting service has its own
[deployment versions](../resources/service.md#runtime-and-deployment-versions).
The target project's identity is supplied separately from this file.

## Example composition

This application has an API and a private Redis service with durable storage.
It assumes `api/Dockerfile` builds an application listening on port 8080 that
uses `CACHE_URL` to connect to Redis.

```yaml
runtime: yaml
default: api-deployment
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

`api-deployment` instantiates `api_definition` as the service `api`;
`cache-deployment` instantiates `cache_definition` as `cache`. Selecting
`api-deployment` includes only `api` in the deployment description. Its
reference to `cache` does not instantiate that service; `cache-deployment`
is a separate target.

The reference names the `cache` instance, and that instance gives its volume
the project-scoped name `cache.data`. The API is publicly exposed; Redis is
reachable within the project's private network.

[Environment and references](../resources/service.md#environment-and-references) explains
resolution between services, including services outside a selected
declaration.

## Validation

Local validation checks the whole file's schema, resource names, individual
service declarations, `from` references, and default target. Composition of
the selected declaration additionally checks instance names, build-source
paths on disk, composed volume names, referenced variables within that
declaration, and reference cycles.

## Generated description

The generated description is JSON with `kind: deployable` and a `services`
array. Each entry contains an instance name, normalized source declaration,
environment templates, and runtime configuration. It contains no remote
project binding, and environment values remain templates until deployment.

The digest identifies that description. Equivalent path spellings, omitted
build defaults, YAML formatting, and mapping or exposure-list ordering do not
change it. An explicit build `target` remains part of the description even
when it names the Dockerfile's last stage. The digest excludes source-file
and image contents and remotely resolved environment values.
