# Resources

A **service definition** describes reusable application configuration.
A **deployment declaration** maps **instance names** to those definitions.
Each instance name identifies a service in the selected remote project;
the definition's name is local to the application description.

`uniac.yaml` represents this description as named resources. The supported
types are `service` and `stateful` for [service definitions](service/overview.md),
and `deployment` for deployment declarations. [Volumes](volume.md) are
declared within service definitions.

## Deployment declarations

A `type: deployment` declaration instantiates service definitions. It creates
no remote service group or environment; each resulting service has its own
[deployment versions](service/overview.md#runtime-and-deployment-versions).

| Field | Meaning |
|---|---|
| `services` | Required, nonempty mapping of instance names to definitions and exposure. |
| `services.<instance>.from` | Required name of an existing `service` or `stateful` definition in this file. |
| `services.<instance>.public_ports` | Optional [public endpoint declarations](service/networking.md#public-endpoints). |

An instance name is one DNS label: lowercase letters, digits and dashes,
starting and ending with a letter or digit, at most 63 characters.

This description instantiates the `server` definition as the remote service
`api`:

```yaml
resources:
  server:
    type: service
    image: mendhak/http-https-echo:31
  application:
    type: deployment
    services:
      api:
        from: server
```

## uniac.yaml

The description file has these top-level fields:

| Field | Meaning |
|---|---|
| `runtime` | Optional; `yaml` is the default and only supported value. |
| `default` | Optional name of a deployment resource to select when none is named explicitly. |
| `resources` | Required, nonempty mapping of resource names to typed definitions. |

Resource names match `^[a-z0-9]+(?:(?:__?|-+)[a-z0-9]+)*$` and are unique
within the file. Every resource requires `type`. Unknown fields are rejected
at every level.

## Validation and generated description

Local validation checks the whole file's schema, resource names, individual
service declarations, `from` references, and default target. Composition of
the selected deployment additionally checks instance names, build-source
paths on disk, composed volume names, referenced variables within the
deployment, and reference cycles. A service definition alone is not a
deployable target.

The generated description is JSON with `kind: deployable` and a `services`
array. Each entry contains an instance name, normalized source declaration,
environment templates, and runtime configuration. It contains no remote
project binding, and environment values remain templates until deployment.

The digest identifies that description. Equivalent path spellings, omitted
build defaults, YAML formatting, and mapping or exposure-list ordering do not
change it. An explicit build `target` remains part of the description even
when it names the Dockerfile's last stage. The digest excludes source-file
and image contents and remotely resolved environment values.
