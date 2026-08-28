
# Authoring `uniac.yaml`

`uniac.yaml` sits at the project root and is the whole static description of a
system. An agent reading one sees the entire architecture; an agent writing one
describes a new architecture. Nearly everything below is enforced by `uniac
plan`, which runs fully offline — write, plan, read the error, fix. Never
guess. The one-service-per-deployment limit is one such exception: a
deployment instantiating two services plans clean, and only `uniac deploy`
rejects it.

Decoding is strict: an unknown key anywhere is a hard error. The field tables
below are therefore exhaustive, and inventing a field (`ports`, `replicas`,
`depends_on`) fails the manifest rather than being ignored.

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
alphanumeric runs joined by interior separators: any run of dashes (`-`, `--`,
`---`, …), or one or two underscores (`_`, `__`) and no more. Separators may
never lead or trail. The grammar is the docker-repository-safe
subset, because instance names become image repository components. The same
grammar constrains service instance names.

## `type: service`

A reusable definition of one workload's shape. Never directly deployable — a
deployment instantiates it.

| Field | Required | Meaning |
|---|---|---|
| `image` | one of | OCI image reference — a prebuilt image the CLI pulls. |
| `build` | one of | A Dockerfile build of your own project tree. See below. |
| `env` | no | Environment variables, `NAME: value`. Values may embed references. |
| `start_command` | no | Overrides the image CMD at the platform layer; the image is untouched. |

A service declares **exactly one** of `image:` or `build:`. Declaring both, or
neither, fails the plan. An empty `image: ""` counts as absent, so `image: ""`
plus `build: .` is a legal build-only service.

There is **no port field on a service** and no public-exposure field: which
instances face the public is a property of the deployment (see `public_ports`).
The internal network is port-transparent, so a purely internal service never
declares the port it binds; only a public claim names it, and it is named on
the deployment's instance, not on the definition.

**Env key grammar** is `^[A-Za-z_][A-Za-z0-9_]*$`. The key `host` is reserved —
it is the builtin `${{self.host}}`, and declaring it is a config error.

### `build:` — building from your own tree

Two spellings. A string names the build root:

```yaml
api:
  type: service
  build: ./api
```

An object refines it. All four keys are optional; no others exist:

```yaml
api:
  type: service
  build:
    root: ./api                          # source tree, relative to uniac.yaml's directory; default "."
    context: ./frontend                  # build context, relative to root; default the root itself
    dockerfile: deploy/Dockerfile.prod   # relative to root; default "Dockerfile"
    target: production                   # multi-stage stage; default the file's last stage
```

There is no build-args, secrets, ssh, platform, cache, or builder-selection
field.

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

`uniac plan` renders a build in both sections — the `Building` line qualifies
only the non-default fields, in the fixed order context, dockerfile, target;
the `Deploying` column carries the bare `build <root>`:

```
Building
  build ./api (context frontend, dockerfile deploy/Dockerfile.prod, target production)

Deploying
  api  build ./api  public: 8080 (http)
```

A pulled service instead renders `pull <ref>` under `Building` and the bare ref
under `Deploying`.

Those rows are the default form: a declaration's `env` and `start_command`
appear only under `uniac plan --full` — see [cli.md](cli.md).

## `type: stateful`

A service the platform runs as **exactly one instance** — the single-writer
condition durable storage needs. It takes the same fields as `type: service`
and is instantiated the same way; the kind is the only difference.

```yaml
db:
  type: stateful
  image: postgres:18-alpine
  env:
    PGDATA: /var/lib/postgresql/data/pgdata
  volumes:
    - name: data
      size_gb: 10
      mount_path: /var/lib/postgresql/data
```

- `uniac plan` marks the instance on its row: `database (stateful)  postgres:18-alpine`.
- In the deployable, the service entry carries `"kind": "stateful"`; a
  stateless service omits the field entirely.

### `volumes:` — durable storage

Only a `type: stateful` service may declare a volume: durable storage needs the
single-writer guarantee. `volumes` is a sequence of mappings, and each entry
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
- **The deployed entity name is the composed `<instance>.<local>`.** A
  definition declaring `name: data`, instantiated as `primary`, yields the
  volume `primary.data`; a second instantiation named `replica` yields
  `replica.data`. No manifest key sets the composed name directly. It must be
  lowercase with one dot and at most 127 characters.

`uniac plan` adds it as a fourth column on the instance row:

```
Deploying
  database (stateful)  postgres:18-alpine  public: 5432 (tcp)  volume: database.data (10GB)
```

What a volume is doing once deployed — size, lifecycle state, which service
holds it — is read back through `uniac status`; see [cli.md](cli.md).

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

Every message below is produced offline, before anything is sent anywhere. Each
is printed as `Error: ` plus the origin that decided it: `uniac.yaml: ` for a
manifest-reader failure — often further qualified `resource "<n>": `,
`service "<n>": `, or `deployment "<d>": instance "<i>": ` — and
`deployment "<d>": ` for a composition failure. Target resolution and the four
build-source existence checks carry no `uniac.yaml: ` prefix; the latter run
after the manifest itself has decoded, against the instantiated service, so
their `service "<n>": ` names the deployment's **instance** — where a
`uniac.yaml: `-prefixed `service "<n>": ` names the definition.

| Condition | Error |
|---|---|
| Unknown field anywhere | `field ports not found in type registry.serviceSchema` |
| Unknown resource `type` | `unknown type "widget" (supported: service, stateful, deployment)` |
| `runtime` other than `yaml` | `runtime "python" is not supported (only "yaml")` |
| Service declaring neither source | `service "a" declares no source (set image: or build:)` |
| Service declaring both sources | `service "a" declares both image and build — a service has one source` |
| `build:` that is neither a string nor a mapping | `resource "a": build: takes a root path or an object; use "." for defaults` |
| Unknown key inside the `build` mapping | `field args not found in type registry.fields` |
| Absolute build path | `service "a": build root: "/abs/path" is absolute — build paths are relative` (likewise `build context:`, `build dockerfile:`) |
| Build path escaping its anchor | `service "a": build root: "../outside" escapes the directory it is declared against` |
| Build root missing on disk | `service "web": build root "api" does not exist` |
| Build context missing on disk | `service "web": build context "api/frontend" does not exist` |
| No Dockerfile, and none named | `service "web": no Dockerfile at the build root . — add one, set build.dockerfile, or set image:` |
| Named dockerfile missing | `service "web": dockerfile "api/deploy/Dockerfile.prod" not found` |
| `volumes` on a non-stateful service | ``service "db" declares volumes but is not stateful — durable storage needs the single-writer guarantee (`type: stateful`)`` |
| More than one volume on a service | `service "db" declares 2 volumes; one volume per service for now` |
| Missing required key in a volume entry | `resource "db": volumes[0]: 'name' is required` (likewise `'size_gb'`, `'mount_path'`) |
| Volume name outside the grammar | `service "db": volume name "pg_data" must be a lowercase label (dashes inside, no dots — the instance name scopes it)` |
| Non-positive size | `service "db": volume "data" needs a positive size_gb` |
| Mount path not a normalized absolute path | `service "db": volume "data": mount_path "data" must be a normalized absolute path (not /)` |
| Unknown key inside a volume entry | `field size not found in type registry.volumeSchema` |
| Composed volume name too long | ``deployment "d": service "<instance>": composed volume name "<instance>.data" does not fit the platform grammar (`<instance>.<local>`, lowercase, one dot, at most 127 chars)`` |
| Reserved env key | `env key "host" is reserved for ${{self.host}}` |
| Malformed reference | `malformed reference at "${{ Bad.VAR }}" — expected ${{service.VAR}} or ${{self.VAR}}` |
| `${{self.X}}` with no such own variable | `env U references ${{self.MISSING}} but no such variable is declared` |
| Reference to an in-set instance's missing variable | `env U references database.NOPE, but "database" declares no such variable (available: host, DATABASE_URL)` |
| Reference chain that never grounds in a literal | `value-resolution cycle a.X → a.Y → a.X never grounds in a literal` |
| Unknown ingress kind | `public port 80 claims unknown exposure kind "grpc" (supported: http, tcp)` |
| Bare integer in `public_ports` | ``cannot unmarshal !!int `8080` into registry.publicPortSchema`` |
| Instance drawing from a missing definition | `instance "a": no service "nope"` |
| Deployment instantiating nothing | `resource "d" must instantiate at least one service` |
| Targeting a service | `resource "api" is a service — services are reusable definitions, not directly deployable; instantiate it in a deployment: …` (a snippet showing the fix follows) |
| `default` naming a service | `default "a" is a service — only deployments are deployable targets` |
| Instance name outside the grammar | `service instance name "Bad-Name-" must match ^[a-z0-9]+(?:(?:__?\|-+)[a-z0-9]+)*$` |
| Manifest with no deployment | `uniac.yaml declares no deployment — services are reusable definitions; add one: …` (a snippet showing the fix follows) |
| Several deployments, no `default` | `uniac.yaml has multiple deployments and no 'default'; name one (have: d1, d2)` |

The bare `build:` key with no value, a non-string scalar such as `build: 5`, and
a sequence all produce the same `takes a root path or an object` message. The
not-stateful gate fires before every other volume rule, and within an entry the
order is name, then `size_gb`, then `mount_path`.

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
      "container": {
        "source": {
          "ref": "mendhak/http-https-echo:31"
        }
      },
      "env": {
        "GREETING": "hello"
      },
      "name": "web",
      "public_ports": [
        {
          "port": 8080,
          "type": "http"
        }
      ],
      "start_command": "node index.js"
    }
  ]
}
```

The container source is a two-arm union. A pulled service carries
`"source": { "ref": "…" }`; a built one carries `"source": { "build": { … } }`,
with every field omitted at its default — so `build: .` serializes as
`"build": {}` and the fully refined form as:

```json
"container": { "source": { "build": {
  "context": "frontend",
  "dockerfile": "deploy/Dockerfile.prod",
  "root": "api",
  "target": "production"
} } }
```

`ref` and `build` are mutually exclusive, and build paths are canonical and
root-relative.

A `type: stateful` service's entry additionally carries `"kind": "stateful"`;
stateless entries omit the field. A declared volume rides on the service as a
single object — never a list, and there is no project-level volume section:

```json
"volume": {
  "mount_path": "/var/lib/postgresql/data",
  "name": "database.data",
  "size_gb": 10
}
```

`volume.name` is the composed entity name, never the local one. The key is
absent for any service that declares no volume.

Its `digest` is the release identity, and it is content-addressed: the services
are name-sorted, claim lists are canonicalized by `(port, type)`, and env keys
are ordered — so reindenting the YAML, reordering resources, or reordering a
claim list produces a byte-identical artifact and the same digest. Compare
digests to answer "did this edit change the system?" without deploying.

Read the deployable, not the YAML, when you need to know what will actually
ship: it is the manifest after every default, resolution, and canonicalization
has been applied.


## Composing a system of services

A project is a **flat list of services on one private network**, each
addressable by its instance name. That is the whole topology model: no groups,
no tiers, no per-environment scoping above the project.

### Shape: one deployment per service

`uniac deploy` rejects a deployment that instantiates more than one service. So
a multi-service system is **several deployments in one manifest**, each shipping
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
uniac deploy database    # provider first
uniac deploy api-web     # then the consumer
```

Keep deployment and instance names aligned with the service they ship, and keep
every service in one manifest and one project — that is what makes the file the
architecture diagram.

Declare a single-writer service — a database, anything owning durable storage —
as `type: stateful`: the platform runs it as exactly one instance (schema in
this document). That is also the only kind that may declare a
`volumes:` block, and the volume it declares is scoped by the *instance*
name: the instance `database` above holds the volume `database.data`. Two
instantiations of one definition therefore hold two distinct volumes. There
is no group construct; a three-node database is three stateful services you
name and wire individually, each with its own address.

### Wiring

**References name the deployed instance, never the definition.** `${{database.X}}`
resolves against the instance named `database`, whatever resource it draws
`from`. Getting this backwards is the most common wiring bug, and it fails
silently: a reference to a name that is not an instance in the deployed set is
treated as a *cross-deployment* reference and passes through.

| Reference | Resolved |
|---|---|
| `${{self.host}}` | The declaring service's own internal hostname. The only builtin. |
| `${{self.VAR}}` | Its own declared variable. Checked at plan time. |
| `${{inst.VAR}}` where `inst` is in the same deployment | Checked at plan time — a missing variable fails the plan. |
| `${{inst.VAR}}` where `inst` is elsewhere in the project | Passes through; the platform resolves it at deploy time against the project's other deployments. **Not checked locally.** |

Because each service gets its own deployment, essentially every cross-service
reference in a real system is the last row: unchecked locally, resolved
remotely. Spell instance names carefully, and confirm with `uniac status` that
the provider is actually running under the name you referenced.

**A dangling reference never fails a deploy.** The affected variable is left
unset and the run returns a warning — it lands as a `warning` row on the
service in the final frame's state block. Check for `warning` rows on every
deploy; an unset `DATABASE_URL` is otherwise a runtime mystery.

**Consumer propagation.** After a successful deploy the platform re-resolves the
project's other services and recreates any whose injected values changed. So
order is a convenience, not a requirement: deploy the consumer first and it
comes up with the variable unset until the provider lands, at which point the
platform recreates it with the real value. Deploying the provider first just
skips the broken window.

**Ports travel through env, not through the manifest.** No service declares the
port it binds; the internal network is port-transparent. A consumer that needs a
concrete port gets it from the provider's own variables — which is why the
`db` definition above exports a whole `DATABASE_URL` rather than a host and a
port for the consumer to reassemble.

### Exposure

Claim public exposure on the **instance**, in the deployment — the same
definition can face the public in one deployment and stay internal in another.

- **Expose the edge, nothing else.** A service holding no public claim is
  reachable only from the project's other services — the correct default for
  databases, caches, workers, and internal APIs. Retracting exposure a
  service already holds is a different edit — deleting the block is not it;
  see the tri-state below.
- **`http`** gives a hostname on the shared edge, terminated by the platform and
  routed to your listen port. Use it for anything speaking HTTP.
- **`tcp`** allocates a public `host:port` and forwards raw TCP to your listen
  port as-is. Use it only when a client cannot speak HTTP; the public port is
  the platform's to choose, so read it back from the service's `endpoint` row
  in `uniac status`.

**Respect the tri-state on redeploys.** Whether a `public_ports` block is
omitted, empty, or spelled out is itself the instruction a redeploy carries,
and the three are not interchangeable — exact semantics in
this document. So never "clean up" a `public_ports` block you did not
intend to change: editing one is an exposure change, and the safest rollout of
new code leaves it alone.

### What the platform provides

- A private network per project; every service addressable by instance name.
- Injection of the resolved `env` at container start — **exactly** that map,
  nothing more.
- Deploy-time resolution of `${{...}}`, and recreation of consumers when a
  provider's values change.
- Public routing for each claim: an HTTP hostname, or an allocated TCP
  `host:port`.
- Provisioning, attaching, and holding the durable volume a `type: stateful`
  service declares; the volume is a project-scoped entity that outlives any
  single deploy.
- Liveness observed on the container process, and a per-service account —
  version, status, replicas, endpoints, holds — readable via `uniac status`.

### What it does not

Do not look for these in `uniac.yaml`; the manifest schema rejects unknown keys,
so an invented field fails the plan rather than being ignored.

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
  `volumes:` block (schema in this document) — but nothing else about
  sizing or placement is.
- **No multiple environments per project.** One project is one running system;
  a second environment is a second project, linked from a different checkout —
  or, for `uniac deploy` only, targeted with `UNIAC_PROJECT_URL`. Details in
  [cli.md](cli.md).

### Operating the system

```sh
uniac status                   # every service and volume the project holds
uniac status api               # one service
```

- The `v<N>` on a service's row numbers the serving deployment — the answer to
  "is this service running what I just shipped?"
- An `endpoint` row's address is the whole string to dial; the trailing
  `→ :<port>` is your own listen port that the traffic lands on, and it
  appears nowhere in the address.
- `hold` rows are platform-side reasons a service is not converging. A service
  that never reaches its expected state with `hold` rows is a platform
  condition, not a manifest bug.
- A service's `volume` row names the volume it mounts and where. The volume's
  own facts — size, and whether it is attached to a service, resting
  unattached with its data intact, or transitional — appear as their own
  `volume` sections, and only in the whole-project `uniac status`;
  `uniac status <service>` omits them. Full row vocabulary in [cli.md](cli.md).
- A service the project runs appears in `status` whether or not the manifest
  still describes it — what is running is not a client's opinion. Deleting a
  resource from `uniac.yaml` does not remove the service; the CLI has no
  removal command, so retire a service from the dashboard.

See [cli.md](cli.md) for the full frame and state-block shape and the exit-code
contract, and this document for the schema and the plan-time rules.
