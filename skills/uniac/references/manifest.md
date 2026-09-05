# `uniac.yaml`

`uniac.yaml` statically declares services and their relationships. It is read
from the project directory. A **service definition** describes reusable application
configuration; a **manifest deployment** selects definitions and gives them **instance
names** that identify the services in a project. Manifest deployments do not
create remote service groups or environments.

Unknown fields are rejected at every level. The tables below describe all
supported fields. The platform's distinct live deployment lifecycle and
runtime behavior are in [platform.md](platform.md).

```yaml
runtime: yaml
default: website
resources:
  server:
    type: service
    image: mendhak/http-https-echo:31
    env:
      GREETING: hello
  website:
    type: deployment
    services:
      web:
        from: server
        public_ports: [{ port: 8080, type: http }]
```

## Top level

| Field | Meaning |
|---|---|
| `runtime` | Optional; `yaml` is the default and only supported value. |
| `default` | Optional deployment name used when a command supplies no target. |
| `resources` | Required, nonempty mapping of names to resource definitions. Each resource requires `type: service`, `type: stateful`, or `type: deployment`. |

Resource and service instance names match
`^[a-z0-9]+(?:(?:__?|-+)[a-z0-9]+)*$`; resource names are unique within the
file. `plan` and `deploy` select the explicitly named deployment, otherwise
`default`, otherwise the only deployment. Multiple deployments without a
default require an explicit target. A service definition cannot be a target.

## Service definitions

`type: service` and `type: stateful` share these fields:

| Field | Meaning |
|---|---|
| `image` | OCI image reference to pull. Exactly one of `image` or `build` is required. |
| `build` | Dockerfile build source, described below. An empty `image: ""` counts as absent. |
| `env` | Optional mapping of environment variable names to string values, which may contain references. |
| `start_command` | Optional string overriding the image CMD at runtime. |
| `volumes` | Optional list of durable volumes; a nonempty list is allowed only with `type: stateful`. |

Environment variable names match `^[A-Za-z_][A-Za-z0-9_]*$`. The name `host`
is reserved for the builtin reference. Service definitions have no port or
exposure field; `public_ports` belongs to each deployment instance.

### Build source

`build: ./api` names the build root. An object accepts these optional fields:

| Field | Relative to | Default |
|---|---|---|
| `root` | Directory containing `uniac.yaml` | `.` |
| `context` | Build root | The root itself |
| `dockerfile` | Build root | `Dockerfile` |
| `target` | Dockerfile stage name | Last stage |

A Dockerfile is required. Its path is relative to the build root even when
`context` names another directory; Dockerfile `COPY` paths use the context.
The Dockerfile may be outside that context. Paths are checked lexically:
`root` must stay within the project directory, and `context` and `dockerfile`
within the root. Absolute or escaping paths fail locally.

The build context comes from the working tree. Only its own `.dockerignore`
filters the build; `.gitignore` does not. The schema has no build arguments,
secrets, SSH forwarding, architecture, or cache settings. Build execution and
Docker requirements are in [cli.md](cli.md).

`build: {}`, `build: "."`, and `build: ""` select the defaults. A bare
`build:` or `build: null` is invalid. Equivalent relative paths and omitted
defaults produce the same planned declaration.

### Volumes

`volumes` is a list containing at most one mapping. All three fields are
required:

| Field | Meaning |
|---|---|
| `name` | Local volume name matching `^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$`: 1–63 lowercase letters, digits, or interior dashes. |
| `size_gb` | Positive YAML number. Integer values express the supported sizes; floats truncate toward zero and quoted numbers are rejected. |
| `mount_path` | Normalized absolute path other than `/`. Trailing slashes, repeated slashes, and `.` or `..` path components are rejected. |

The resulting name `<instance>.<name>` is limited to 127 characters.
Omitting `volumes`, writing `volumes: []`, or writing a bare `volumes:` all
declare no volume. Persistence, reuse, and deletion are described under
[storage](platform.md#storage).

## Deployments

`type: deployment` accepts:

| Field | Meaning |
|---|---|
| `services` | Required, nonempty mapping of instance names to definitions and exposure. |
| `services.<instance>.from` | Required name of an existing `service` or `stateful` definition in this manifest. |
| `services.<instance>.public_ports` | Optional list of public exposure requests, described below. |

One definition can be instantiated under multiple names. The schema accepts
multiple instances in one deployment; execution limits belong to
[CLI deployment](cli.md#deployment). Separate deployment targets can place
services in the same remote project.

### Public exposure

Each `public_ports` entry is a mapping with two required fields:

| Field | Meaning |
|---|---|
| `port` | The application's listen port, as a YAML number. |
| `type` | `http` or `tcp`. |

A bare port number is invalid. Local validation checks the fields and type;
the platform checks port ranges and exposure limits. Address allocation and
protocol behavior are in [platform.md](platform.md#networking).

The list has three meanings on deployment:

| Value | Result |
|---|---|
| Omitted or `null` | Keeps the service's existing public exposure. |
| `[]` | Removes all public exposure. |
| Nonempty list | Replaces public exposure with exactly this list. |

## Environment references

Environment values are plaintext. The manifest has no secrets management or
external-secret reference mechanism.

References occur inside `env` values, with this grammar:

```text
\$\{\{\s*([a-z0-9][a-z0-9_-]*|self)\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}
```

`${{database.DATABASE_URL}}` names the variable on the instance `database`,
independently of its definition name. `${{self.VAR}}` names a variable on the
declaring service. `host` is the only builtin: `${{self.host}}` and
`${{database.host}}` refer to the respective service's internal hostname.
References may be embedded in larger strings, such as
`http://${{self.host}}:8080`.

Chains resolve transitively. `self` always belongs to the service that
declared the value: reading another service's exported URL retains that
service's host and variables. There is no escape syntax; every `${{` opener
must form a valid reference.

References to `self` must name a builtin or a declared variable. For instances
within the selected deployment, local validation also checks referenced
variables and cycles. A name outside that deployment passes through for remote
resolution, even if another deployment in the file defines it. Runtime
resolution and missing-variable behavior are in
[platform.md](platform.md#environment).

## Planning and the generated artifact

`uniac plan` is offline and checks:

- The whole manifest's schema, names, individual service declarations,
  `from` references, and default target.
- For the selected deployment, the existence of build roots, contexts, and
  Dockerfiles, composed volume names, referenced variables within the
  deployment, and reference cycles.

It does not build images, verify application startup, resolve references to
other deployments, or enforce platform policy. Selecting one deployment does
not perform the second set of checks on other deployments. Deploy uses this
same planning before any remote action.

The generated service description contains instance names, normalized source
declarations, environment templates, and runtime configuration. It contains
no remote project binding, and environment values remain templates until
deploy. The [CLI](cli.md#output-and-exit-codes) can emit it as JSON.

The digest identifies that description. Equivalent path spellings, omitted
build defaults, YAML formatting, and mapping or exposure-list ordering do not
change it. It excludes source-file contents and remotely resolved values: editing a
Dockerfile, application code, or an image behind an unchanged tag can change
the deployed application without changing this digest.
