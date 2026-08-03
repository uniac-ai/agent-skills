---
name: uniac-multi-service
description: Compose several services into one system on Uniac — how to shape a manifest when a deployment can ship only one service, wiring services with cross-deployment ${{...}} references, choosing public exposure, deploy ordering and consumer propagation, and what the platform does not provide. Load when a Uniac project has more than one service, or when a service must reach another.
---

# A system of services on Uniac

A project is a **flat list of services on one private network**, each
addressable by its instance name. That is the whole topology model: no groups,
no tiers, no per-environment scoping above the project.

## Shape: one deployment per service

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
      DATABASE_URL: "postgres://postgres:${{self.POSTGRES_PASSWORD}}@${{self.host}}:5432/app"

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
`[[uniac-manifest]]`). There is no group construct; a three-node database is
three stateful services you name and wire individually, each with its own
address.

## Wiring

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

## Exposure

Claim public exposure on the **instance**, in the deployment — the same
definition can face the public in one deployment and stay internal in another.

- **Expose the edge, nothing else.** A service with no `public_ports` is
  reachable only from the project's other services. That is the correct default
  for databases, caches, workers, and internal APIs.
- **`http`** gives a hostname on the shared edge, terminated by the platform and
  routed to your listen port. Use it for anything speaking HTTP.
- **`tcp`** allocates a public `host:port` and forwards raw TCP to your listen
  port as-is. Use it only when a client cannot speak HTTP; the public port is
  the platform's to choose, so read it back from the service's `endpoint` row
  in `uniac status`.

**Respect the tri-state on redeploys.** Omitting `public_ports` inherits the
serving deployment's claims, which is what makes a code-only rollout safe.
Writing `[]` actively retracts all exposure. Writing a claim set restates it in
full — so dropping one entry from a two-entry list removes that exposure. Never
"clean up" a `public_ports` block you did not intend to change.

## What the platform provides

- A private network per project; every service addressable by instance name.
- Injection of the resolved `env` at container start — **exactly** that map,
  nothing more.
- Deploy-time resolution of `${{...}}`, and recreation of consumers when a
  provider's values change.
- Public routing for each claim: an HTTP hostname, or an allocated TCP
  `host:port`.
- Liveness observed on the container process, and a per-service account —
  version, status, replicas, endpoints, holds — readable via `uniac status`.

## What it does not

Do not look for these in `uniac.yaml`; the manifest schema rejects unknown keys,
so an invented field fails the plan rather than being ignored.

- **No health checks or readiness probes.** No port is declared, so none can be
  probed. Liveness is the container process. Your own retry and readiness logic
  is your own.
- **No dependency ordering.** There is no `depends_on`. A consumer must tolerate
  a provider that is not up yet — the deploy order is yours to sequence, and
  propagation may restart it later regardless.
- **No build from source.** Services name prebuilt OCI images. Build and publish
  in your own pipeline, then reference an immutable tag or digest.
- **No secrets management.** `env` values are plaintext in the manifest.
  Reference a provider service's variable rather than repeating a credential,
  and keep genuinely sensitive material out of a committed manifest.
- **No volumes, replica counts, resource limits, or scaling controls** in the
  manifest.
- **No multiple environments per project.** One project is one running system;
  a second environment is a second project, linked from a different checkout
  (or selected with `UNIAC_PROJECT_URL`).

## Operating the system

```sh
uniac status                   # every service: version, status, endpoints, holds
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
- A service the project runs appears in `status` whether or not the manifest
  still describes it — what is running is not a client's opinion. Deleting a
  resource from `uniac.yaml` does not remove the service; the CLI has no
  removal command, so retire a service from the dashboard.

See `[[uniac-cli]]` for the full frame and state-block shape and the exit-code
contract, and `[[uniac-manifest]]` for the schema and the plan-time rules.
