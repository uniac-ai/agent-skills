
# Authoring `uniac.yaml`

`uniac.yaml` sits at the project root and is the whole static description of a
system. Decoding is strict: an unknown key anywhere is a hard error, so the
field tables below are exhaustive, and inventing a field (`ports`, `replicas`,
`depends_on`) fails the manifest rather than being ignored. Nearly everything
below is enforced by `uniac plan`, which runs fully offline; the exceptions —
among them the one-service-per-deployment limit, cross-deployment references,
and the platform-side public-port rules — are called out where they arise.

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

**Resource names** match `^[a-z0-9]+(?:(?:__?|-+)[a-z0-9]+)*$` — the
docker-repository-safe subset, because instance names become image repository
components. The same grammar constrains service instance names.

## `type: service`

| Field | Required | Meaning |
|---|---|---|
| `image` | one of | OCI image reference — a prebuilt image the CLI pulls. |
| `build` | one of | A Dockerfile build of your own project tree. See below. |
| `env` | no | Environment variables, `NAME: value`. Values may embed references. |
| `start_command` | no | Overrides the image CMD at the platform layer; the image is untouched. |

A service declares **exactly one** of `image:` or `build:`; an empty
`image: ""` counts as absent, so `image: ""` plus `build: .` is a legal
build-only service.

There is **no port field on a service** and no public-exposure field: the
internal network is port-transparent, so a purely internal service never
declares the port it binds, and which instances face the public is a property
of the deployment (see `public_ports`).

**Env key grammar** is `^[A-Za-z_][A-Za-z0-9_]*$`. The key `host` is reserved —
it is the builtin `${{self.host}}`, and declaring it is a config error.

### `build:` — building from your own tree

Two spellings. A string names the build root:

```yaml
api:
  type: service
  build: ./api
```

An object refines it. All four keys are optional, and no others exist — there
is no build-args, secrets, ssh, platform, cache, or builder-selection field:

```yaml
api:
  type: service
  build:
    root: ./api                          # source tree, relative to uniac.yaml's directory; default "."
    context: ./frontend                  # build context, relative to root; default the root itself
    dockerfile: deploy/Dockerfile.prod   # relative to root; default "Dockerfile"
    target: production                   # multi-stage stage; default the file's last stage
```

- **A Dockerfile is required** — `<root>/Dockerfile` by default, or
  `<root>/<dockerfile>`. There is no zero-config or autodetect build.
- **The dockerfile anchors at the root, not the context.** This is docker's
  `-f Dockerfile ./frontend` pattern, and it differs from docker-compose: with
  `context:` set and no `dockerfile:`, the CLI looks for `<root>/Dockerfile`,
  not `<context>/Dockerfile`. A dockerfile outside the context still works;
  `COPY` still resolves only against the context.
- **All three paths are lexically confined.** `root` to the project directory;
  `context` and `dockerfile` to the root. Absolute or escaping paths fail at
  plan time.
- **The context is materialized verbatim from your tree.** `.gitignore` does
  not filter it — only the **context** directory's own `.dockerignore` does. A
  gitignored file is still copied.
- **Spellings canonicalize.** `./api`, `api`, `api/` and `{ root: api }` are one
  declaration with one digest, and `dockerfile: Dockerfile` is byte-identical to
  omitting it. `build: {}`, `build: "."` and `build: ""` are all the
  all-defaults build of the project directory.
- **The digest names the declaration, not the source content.** Editing the
  Dockerfile does not move it; only a manifest change does.
- **No manifest field chooses a build platform.** The architecture a build
  targets, and when it runs, are deploy-time behavior — see [cli.md](cli.md).

`uniac plan` previews the resolved build; `uniac plan --full` adds each
declaration's `env` and `start_command`.

## `type: stateful`

A service the platform runs as **exactly one instance** — the single-writer
condition durable storage needs. Otherwise it is a `type: service`: the same
fields, instantiated the same way, plus the `volumes:` block below.

### `volumes:` — durable storage

Only a `type: stateful` service may declare a volume — the single-writer
guarantee is the point. `volumes` is a sequence of mappings, and each entry
takes exactly these three keys, all required:

| Key | Meaning |
|---|---|
| `name` | Local label, `^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$` — lowercase alphanumerics with dashes strictly inside, 1–63 characters. No dots, no underscores, no uppercase. |
| `size_gb` | A YAML number of at least 1. A float decodes and truncates toward zero (`2.99` → 2GB, `0.5` → rejected as non-positive) — write an integer. A quoted `"10"` is a decode error. |
| `mount_path` | Normalized absolute path, and not `/`. `data`, `./data`, `/data/`, `/data//x` and `/data/../etc` are all rejected. |

- **At most one volume per service.**
- `volumes: []` and a bare `volumes:` with no value both mean no volume,
  byte-identical to omitting the key. There is no "explicit empty claim"
  meaning here, unlike `public_ports: []`.
- **The deployed entity name is the composed `<instance>.<local>`** —
  lowercase with one dot, at most 127 characters, and set by no manifest key
  directly. A definition declaring `name: data`, instantiated as `primary`,
  yields the volume `primary.data`; a second instantiation named `replica`
  yields `replica.data`.

Once deployed the volume is a project-scoped entity that outlives any single
deploy; what it is doing — size, lifecycle state, which service holds it — is
read back through `uniac status`; see [cli.md](cli.md).

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
- **`self`** is the reflexive scope — the declaring service's own builtins and
  variables — and **`host`** is the only builtin: the platform-allocated
  internal hostname, the one fact the platform contributes to the environment.
- **Chains resolve transitively, and `self` stays bound to the service that
  *declared* the value, never the one that referenced it.** A consumer reading
  `${{database.DATABASE_URL}}` therefore receives the database's own host and
  password — which is what makes the exported-URL pattern below work.
- **Names resolve at plan time; values resolve at deploy time**, by the
  platform, and are injected at container start — **exactly** the resolved
  map, nothing more.
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

A deployment instantiating more than one service parses and plans fine;
`uniac deploy` currently rejects it — for the exit status and the message, see
[cli.md](cli.md). Compose a multi-service system as several deployments — see
Composing a system of services, below.

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
are enforced there, so they pass `plan`. A `tcp` exposure's public port and
hostname are allocated by the platform — the manifest names only your own
listen port.

**The claim set is tri-state, and the distinction matters on every redeploy:**

| Written | Meaning |
|---|---|
| omitted | Claims nothing. The platform keeps the serving deployment's claims, so a code-only rollout never drops exposure. |
| `[]` | Claims nothing *and converges* the instance to no public exposure of any kind. |
| present | Restates the full claim set; the result is exactly what is listed. |

## What fails at plan time

`uniac plan` decodes the whole manifest offline and exits 1 on the first
failure, naming the rule and the resource that broke it. **It resolves only the
deployment it targets**: schema and decode errors surface from any resource,
but the build-source and reference checks below run on that one deployment
alone — so a multi-deployment manifest is verified only by planning each
deployment by name, never by a bare `uniac plan`. Three checks are not
visible in the schema above: it stats the build sources on disk (`root`,
`context`, and the Dockerfile must exist); a reference chain must ground in a
literal, so a resolution cycle fails; and only a deployment is a deployable
target, whether named as `default` or as the argument. Run `uniac plan` to see
the exact message.

What is **not** checked locally: any reference to a name outside the deployed
set. It passes through by design, and a dangling one surfaces at deploy time as
a warning with the variable left unset — never as a failure. See Wiring, below.

## The deployable

`uniac plan --json` prints `{resource, digest, deployable}`. The deployable is
the canonical, target-free artifact the platform consumes — the manifest after
every default, resolution, and canonicalization has been applied. Read it, not
the YAML, when you need to know what will actually ship; run the command to see
its shape. Build paths in the artifact are canonical and root-relative, and
defaults are omitted rather than spelled out — so distinct spellings of one
declaration serialize identically.

Its `digest` is the release identity, and it is content-addressed: the services
are name-sorted, claim lists are canonicalized by `(port, type)`, and env keys
are ordered — so reindenting the YAML, reordering resources, or reordering a
claim list produces a byte-identical artifact and the same digest. Compare
digests to answer "did this edit change the system?" without deploying.

## Composing a system of services

A project is a **flat list of services on one private network**, each
addressable by its instance name. That is the whole topology model: no groups,
no tiers, no per-environment scoping above the project.

### Shape: one deployment per service

`uniac deploy` ships one service per deployment (the rejection above), so a
multi-service system is **several deployments in one manifest**, each shipping
one service, deployed one at a time into the same project:

```yaml
runtime: yaml
default: api-web        # a deployment — naming a service here is an error
resources:
  # ---- definitions ----
  db:
    type: stateful
    image: postgres:16
    env:
      POSTGRES_PASSWORD: "change-me"
      PGDATA: "/var/lib/postgresql/data/pgdata"   # below the mount: a fresh volume is not empty
      DATABASE_URL: "postgres://postgres:${{self.POSTGRES_PASSWORD}}@${{self.host}}:5432/app"
    volumes:
      - name: data
        size_gb: 10
        mount_path: /var/lib/postgresql/data

  api:
    type: service
    image: ghcr.io/acme/api:1.4.0
    env:
      DATABASE_URL: "${{database.DATABASE_URL}}"   # → the *instance* named `database`
      PORT: "8080"

  # ---- one deployment per service ----
  database:
    type: deployment
    services:
      database: { from: db }

  api-web:
    type: deployment
    services:
      api:
        from: api
        public_ports: [{ port: 8080, type: http }]
```

```sh
uniac plan database; uniac plan api-web   # verify each deployment by name
uniac deploy database                     # provider first
uniac deploy api-web                      # then the consumer
```

Keep deployment and instance names aligned with the service they ship, and keep
every service in one manifest and one project — that is what makes the file the
architecture diagram. Declare a single-writer service — a database, anything
owning durable storage — as `type: stateful` (schema above); its volume is
scoped by the *instance* name, so the instance `database` above holds
`database.data`. There is no group construct: a three-node database is three
stateful services you name and wire individually, each with its own address.

### Wiring

**References name the deployed instance, never the definition** (the scope
rule above). Getting this backwards is the most common wiring bug, and it
fails silently: a reference to a name that is not an instance in the deployed
set is treated as a *cross-deployment* reference and passes through. Because
each service gets its own deployment, essentially every cross-service reference
in a real system is exactly that: unchecked locally, resolved remotely. Spell
instance names carefully, and confirm with `uniac status` that the provider is
actually running under the name you referenced.

**A dangling reference never fails a deploy.** The variable is left unset and
the run warns. Check every deploy for warnings — an unset `DATABASE_URL` is
otherwise a runtime mystery. See [cli.md](cli.md).

**Consumer propagation.** After a successful deploy the platform re-resolves the
project's other services and recreates any whose injected values changed. So
order is a convenience, not a requirement: deploy the consumer first and it
comes up with the variable unset until the provider lands, at which point the
platform recreates it with the real value. Deploying the provider first just
skips the broken window.

**Ports travel through env, not through the manifest.** A consumer that needs a
concrete port gets it from the provider's own variables — which is why the `db`
definition above exports a whole `DATABASE_URL` rather than a host and a port
for the consumer to reassemble.

### Exposure

Exposure is claimed per instance by `public_ports`, above. Operationally:

- **Expose the edge, nothing else.** A service holding no public claim is
  reachable only from the project's other services — the correct default for
  databases, caches, workers, and internal APIs.
- Use `http` for anything speaking HTTP. Use `tcp` only when a client cannot
  speak HTTP, and read the allocated public `host:port` back with
  `uniac status`.
- **Respect the tri-state on redeploys.** Whether a `public_ports` block is
  omitted, empty, or spelled out is itself the instruction a redeploy carries,
  and the three are not interchangeable. So never "clean up" a `public_ports`
  block you did not intend to change: editing one is an exposure change, and
  the safest rollout of new code leaves it alone. Retracting exposure a
  service already holds is a different edit — deleting the block is not it.

### What the platform does not provide

Do not look for these in `uniac.yaml` — decoding is strict (above), so an
invented field fails the plan.

- **No health checks or readiness probes.** No port is declared, so none can be
  probed. Liveness is the container process. Your own retry and readiness logic
  is your own.
- **No dependency ordering.** There is no `depends_on`. A consumer must tolerate
  a provider that is not up yet — the deploy order is yours to sequence, and
  propagation may restart it later regardless.
- **No secrets management.** `env` values are plaintext in the manifest.
  Reference a provider service's variable rather than repeating a credential,
  and keep genuinely sensitive material out of a committed manifest.
- **No replica counts, resource limits, or scaling controls** in the manifest.
  Durable storage *is* declarable — a `type: stateful` service takes a
  `volumes:` block (schema above) — but nothing else about sizing or placement
  is.
- **No multiple environments per project.** One project is one running system;
  a second environment is a second project, linked from a different checkout —
  or, for `uniac deploy` only, targeted with `UNIAC_PROJECT_URL`. Details in
  [cli.md](cli.md).

### Operating the system

`uniac status` reports every service and volume the project holds;
`uniac status <service>` narrows to one. Two readings matter against the
manifest: a service that never reaches its expected state is a platform
condition, not a manifest bug; and a service the project runs appears in
`status` whether or not the manifest still describes it — what is running is
not a client's opinion. Row vocabulary is in [cli.md](cli.md). Deleting a
resource from `uniac.yaml` does not remove the service; the CLI has no removal
command, so retire a service from the dashboard.
