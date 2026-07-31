---
name: uniac-manifest
description: Author uniac.yaml — the complete manifest schema for Uniac projects: resources, type service, type deployment, public_ports and their tri-state semantics, the ${{service.VAR}} reference grammar, and every rule the CLI enforces at plan time. Load whenever a task reads, writes, reviews, or debugs a uniac.yaml.
---

# Authoring `uniac.yaml`

`uniac.yaml` sits at the project root and is the whole static description of a
system. An agent reading one sees the entire architecture; an agent writing one
describes a new architecture. Everything below is enforced by `uniac plan`,
which runs fully offline — write, plan, read the error, fix. Never guess.

Decoding is strict: an unknown key anywhere is a hard error. The field tables
below are therefore exhaustive, and inventing a field (`ports`, `replicas`,
`volumes`, `depends_on`) fails the manifest rather than being ignored.

```yaml
runtime: yaml
default: shop
resources:
  worker:
    type: service
    image: "mendhak/http-https-echo:31"
    env:
      GREETING: hello

  shop:
    type: deployment
    services:
      web:
        from: worker
        public_ports: [{ port: 8080, type: http }]
```

## Top level

| Field | Meaning |
|---|---|
| `runtime` | Manifest runtime. `yaml` is the only supported value, and the default. |
| `default` | The resource `uniac plan` / `uniac deploy` act on when none is named. |
| `resources` | Named map of typed resources — the system description. |

Target resolution for both commands: the named resource, else `default`, else
the manifest's only deployment. With several deployments and no `default`, the
run fails and lists them.

**Resource names** match `^[a-z0-9]+(?:(?:__?|-+)[a-z0-9]+)*$` — lowercase
alphanumeric runs joined by interior separators (`-`, `--`, `_`, `__`).
Separators may never lead or trail. The grammar is the docker-repository-safe
subset, because instance names become image repository components. The same
grammar constrains service instance names.

## `type: service`

A reusable definition of one workload's shape. Never directly deployable — a
deployment instantiates it.

| Field | Required | Meaning |
|---|---|---|
| `image` | yes | OCI image reference. Prebuilt only: there is no build-from-source field. |
| `env` | no | Environment variables, `NAME: value`. Values may embed references. |
| `start_command` | no | Overrides the image CMD at the platform layer; the image is untouched. |

There is **no port field on a service** and no public-exposure field: which
instances face the public is a property of the deployment (see `public_ports`).
The internal network is port-transparent, so the port your process binds is
never declared to Uniac at all.

**Env key grammar** is `^[A-Za-z_][A-Za-z0-9_]*$`. The key `host` is reserved —
it is the builtin `${{self.host}}`, and declaring it is a config error.

## References — `${{service.VAR}}`

One grammar everywhere, embedded inside env-value strings:

```
\$\{\{\s*([a-z0-9][a-z0-9_-]*|self)\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}
```

```yaml
env:
  OWN_URL:      "http://${{self.host}}:8080"        # own builtin
  GREETING_ALT: "${{self.GREETING}}"                # own variable
  DB_HOST:      "${{database.host}}"                # another instance's builtin
  DATABASE_URL: "${{database.DATABASE_URL}}"        # another instance's variable
```

- **Scope names an instance, not a definition.** `${{database.X}}` names the
  deployment's instance `database`, not the service resource it draws `from`.
- **`self`** is the reflexive scope: the declaring service's own builtins and
  variables.
- **`host`** is the only builtin — the platform-allocated internal hostname, the
  one fact the platform contributes to the environment.
- **Names resolve at plan time; values resolve at deploy time**, by the platform,
  and are injected at container start.
- **A reference to a name outside the deployed set passes through** unresolved
  and is resolved remotely against the project's other deployments. This is how
  services in separate deployments wire together — and it is why a typo in a
  cross-deployment reference cannot be caught locally.
- **No escape syntax exists.** Any `${{` that does not parse as a reference is
  an error, so a literal `${{` cannot appear in an env value.

## `type: deployment`

Instantiates services and resolves to the deployable.

```yaml
shop:
  type: deployment
  services:
    web:  { from: worker }        # instance "web", from definition "worker"
    web2: { from: worker }        # same definition, second instance
```

| Field | Meaning |
|---|---|
| `services` | Map of instance name → instantiation. At least one is required. |
| `services.<name>.from` | The service resource this instance instantiates. Required. |
| `services.<name>.public_ports` | Public-exposure claim set for this instance. Tri-state, below. |

`uniac deploy` currently rejects a deployment instantiating more than one
service ("multi-service deployments are not yet supported"); it parses and
plans fine. Compose a multi-service system as several deployments — see
`[[uniac-multi-service]]`.

### `public_ports`

Exposure is declared on the **instance**, because it is a property of the
topology: the same definition can face the public in one deployment and stay
internal in another. Each claim is an object naming your process's own listen
port and the kind of ingress:

```yaml
services:
  api:
    from: api
    public_ports:
      - { port: 8080, type: http }   # a hostname on the shared edge
      - { port: 5432, type: tcp }    # raw TCP behind an allocated public host:port
```

| Form | Meaning |
|---|---|
| `{ port: N, type: http }` | The platform terminates HTTP and routes its hostname to port `N`. |
| `{ port: N, type: tcp }` | The platform allocates a public `host:port` and forwards raw TCP to `N` as-is. |
| `N` (bare integer) | Rejected at parse. A number cannot say which kind of ingress it wants. |

Both keys are required by presence; an unknown `type` is rejected locally.
Ranges (1..65535) and the at-most-one-port-per-type cap are platform policy and
are enforced there, so they pass `plan`.

**The claim set is tri-state, and the distinction matters on every redeploy:**

| Written | Meaning |
|---|---|
| omitted | Claims nothing. The platform keeps the serving deployment's claims, so a code-only rollout never drops exposure. |
| `[]` | Claims nothing *and converges* the instance to no public exposure of any kind. |
| present | Restates the full claim set; the result is exactly what is listed. |

The public port and hostname of a `tcp` exposure are allocated by the platform.
The manifest names only your own listen port.

## What fails at plan time

Every message below is produced offline, before anything is sent anywhere.

| Condition | Error |
|---|---|
| Unknown field anywhere | `field ports not found in type registry.serviceSchema` |
| Unknown resource `type` | `unknown type "widget" (supported: service, deployment)` |
| `runtime` other than `yaml` | `runtime "python" is not supported (only "yaml")` |
| Service with no `image` | `service "a" declares no image` |
| Reserved env key | `env key "host" is reserved for ${{self.host}}` |
| Malformed reference | `malformed reference at "${{ Bad.VAR }}" — expected ${{service.VAR}} or ${{self.VAR}}` |
| `${{self.X}}` with no such own variable | `env U references ${{self.MISSING}} but no such variable is declared` |
| Reference to an in-set instance's missing variable | `env U references database.NOPE, but "database" declares no such variable (available: host, DATABASE_URL)` |
| Reference chain that never grounds in a literal | `value-resolution cycle a.X → a.Y → a.X never grounds in a literal` |
| Unknown ingress kind | `public port 80 claims unknown exposure kind "grpc" (supported: http, tcp)` |
| Bare integer in `public_ports` | `cannot unmarshal !!int 8080 into registry.publicPortSchema` |
| Instance drawing from a missing definition | `instance "a": no service "nope"` |
| Deployment instantiating nothing | `resource "d" must instantiate at least one service` |
| Targeting a service | `resource "api" is a service — services are reusable definitions, not directly deployable` |
| `default` naming a service | `default "a" is a service — only deployments are deployable targets` |
| Instance name outside the grammar | `service instance name "Bad-Name-" must match ^[a-z0-9]+(?:(?:__?\|-+)[a-z0-9]+)*$` |
| Manifest with no deployment | `uniac.yaml declares no deployment — services are reusable definitions` |
| Several deployments, no `default` | `uniac.yaml has multiple deployments and no 'default'; name one (have: d1, d2)` |

What is **not** checked locally: any reference to a name outside the deployed
set. It passes through by design, and a dangling one surfaces at deploy time as
a warning with the variable left unset — never as a failure.

## The deployable

`uniac plan --json` prints `{resource, digest, deployable}`. The deployable is
the canonical, target-free artifact the platform consumes:

```json
{
  "kind": "deployable",
  "services": [
    {
      "name": "web",
      "container": { "source": { "ref": "mendhak/http-https-echo:31" } },
      "env": { "GREETING": "hello" },
      "public_ports": [{ "port": 8080, "type": "http" }],
      "start_command": "…"
    }
  ]
}
```

Its `digest` is the release identity, and it is content-addressed: the services
are name-sorted, claim lists are canonicalized by `(port, type)`, and env keys
are ordered — so reindenting the YAML, reordering resources, or reordering a
claim list produces a byte-identical artifact and the same digest. Compare
digests to answer "did this edit change the system?" without deploying.

Read the deployable, not the YAML, when you need to know what will actually
ship: it is the manifest after every default, resolution, and canonicalization
has been applied.
