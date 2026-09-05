# `uniac.yaml`

In `uniac.yaml`, a **service definition** describes reusable application
configuration; a **manifest deployment** selects definitions and gives them
**instance names** that identify the services in a project. Manifest
deployments do not create remote service groups or environments.

Unknown fields are rejected at every level. The tables below describe all
supported fields. The platform's distinct live deployment lifecycle and
runtime behavior are in [platform.md](platform.md).

## Top level

| Field | Meaning |
|---|---|
| `runtime` | Optional; `yaml` is the default and only supported value. |
| `default` | Optional name of a deployment resource. |
| `resources` | Required, nonempty mapping of names to resource definitions. Each resource requires `type: service`, `type: stateful`, or `type: deployment`. |

Resource and service instance names match
`^[a-z0-9]+(?:(?:__?|-+)[a-z0-9]+)*$`; resource names are unique within the
file. Target selection is described in
[planning and deployment](cli.md#planning-and-deployment).

## Service definitions

`type: service` and `type: stateful` share these fields. Exactly one of
`image` or `build` is required; an empty `image: ""` counts as absent.

| Field | Meaning |
|---|---|
| `image` | OCI image reference. |
| `build` | Dockerfile build source, described below. |
| `env` | Optional mapping of environment variable names to string values, which may contain references. |
| `start_command` | Optional string overriding the image CMD at runtime. |
| `volumes` | Optional list of durable volumes; a nonempty list is allowed only with `type: stateful`. |

Environment variable names match `^[A-Za-z_][A-Za-z0-9_]*$`. The name `host`
is reserved for the builtin reference.

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
project directory, and `context` and `dockerfile` within the root.

Build execution and Docker requirements are in
[CLI planning and deployment](cli.md#planning-and-deployment).

### Volumes

At most one volume may be declared. Each entry is a mapping with three
required fields:

| Field | Meaning |
|---|---|
| `name` | Local volume name matching `^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$`. |
| `size_gb` | YAML number whose value, after truncation toward zero, is at least 1. |
| `mount_path` | Normalized absolute path other than `/`. |

The resulting name `<instance>.<name>` is limited to 127 characters.
A null `volumes` value declares no volume. Persistence, reuse, and deletion
are described under [storage](platform.md#storage).

## Deployments

`type: deployment` accepts:

| Field | Meaning |
|---|---|
| `services` | Required, nonempty mapping of instance names to definitions and exposure. |
| `services.<instance>.from` | Required name of an existing `service` or `stateful` definition in this manifest. |
| `services.<instance>.public_ports` | Optional list of public exposure requests, described below. |

Execution limits are in
[CLI planning and deployment](cli.md#planning-and-deployment).

### Public exposure

Each `public_ports` entry is a mapping with two required fields:

| Field | Meaning |
|---|---|
| `port` | The application's listen port, as a YAML number. |
| `type` | `http` or `tcp`. |

The list has three meanings on deployment:

| Value | Result |
|---|---|
| Omitted or `null` | Keeps the service's existing public exposure. |
| `[]` | Removes all public exposure. |
| Nonempty list | Replaces public exposure with exactly this list. |

Address allocation, protocol behavior, and platform limits are in
[platform.md](platform.md#networking).

## Environment references

Environment values are plaintext and can contain references with this grammar:

```text
\$\{\{\s*([a-z0-9][a-z0-9_-]*|self)\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}
```

A reference's scope names a service instance, independently of its
definition name. `${{self.VAR}}` names a variable on the declaring service.
`host` is the only builtin and means the referenced service's internal hostname.

Chains resolve transitively. Across a chain, `self` remains bound to the
service that declared each value. There is no escape syntax; every `${{` opener
must form a valid reference.

References to `self` must name a builtin or a declared variable.
A name outside the selected deployment passes through for remote
resolution, even if another deployment in the file defines it. Runtime
resolution and missing-variable behavior are in
[platform.md](platform.md#environment).

## Validation and generated description

Local validation checks:

- The whole manifest's schema, names, individual service declarations,
  `from` references, and default target.
- For the selected deployment, the existence of build roots, contexts, and
  Dockerfiles, composed volume names, referenced variables within the
  deployment, and reference cycles.

The generated service description contains instance names, normalized source
declarations, environment templates, and runtime configuration. It contains
no remote project binding, and environment values remain templates until
deploy. The [CLI](cli.md#output) can emit it as JSON.

The digest identifies that description. Equivalent path spellings, omitted
build defaults, YAML formatting, and mapping or exposure-list ordering do not
change it. The digest excludes source-file and image contents and remotely
resolved environment values.
