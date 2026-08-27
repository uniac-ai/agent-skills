---
name: uniac-app
description: Build and run an application on Uniac, the cloud deployment platform — the mental model, the project loop, and what the platform owns versus what you own. Load on any signal that a task deploys to Uniac, reads or writes a uniac.yaml, or runs the uniac CLI; over-trigger by design, because the alternative is answering from memory that contains no Uniac.
---

# Building on Uniac

You describe a system in one `uniac.yaml`, the `uniac` CLI resolves it into a
**deployable** and ships container images — pulled, or built from your own
tree — to a remote **project**, and the platform runs them: it injects each
service's resolved environment, places the containers on a private network
addressable by service name, and allocates public addresses for whatever you
claimed. Nothing of Uniac ships inside your image — your container is entirely
your own.

This skill and its siblings describe Uniac from outside. They assume no access
to Uniac's own source, and they cover the current CLI surface only.

## The three nouns

**Service** — a reusable *definition* of one workload's shape: which image,
which environment variables, which start command. A service is never directly
deployable. Targeting one is an error. A definition is `type: service`, or
`type: stateful` for a workload the platform runs as exactly one instance —
the single-writer condition a database needs. A `type: stateful` service is
also the only kind that can declare a durable volume.

**Deployment** — an *instantiation*: a map of instance names to the definitions
they draw from, plus the public exposure claimed for each instance. Resolving a
deployment yields the deployable, the thing the platform consumes.

**Project** — the remote destination, bound to your directory by `uniac link`
(`.uniac/deploy.json`). A project is a flat list of running services; the
platform holds no grouping above them. Deployments are a client-side
composition resolved on the way in, so the platform never sees one.

The separation is the point: one definition can be instantiated many times, in
many deployments, and a deployment job stays independent of the definitions it
draws from.

**The instance name is the identity.** It is the deployed service's name, its
internal hostname, its platform identity, a component of its image repository,
and the name every `${{...}}` reference resolves against. The definition's name
is only a local label for `from:`.

```yaml
runtime: yaml
default: shop
resources:
  worker:                                 # definition
    type: service
    image: "mendhak/http-https-echo:31"
    env:
      GREETING: hello

  shop:                                   # deployment
    type: deployment
    services:
      web:                                # instance name — the deployed identity
        from: worker
        public_ports: [{ port: 8080, type: http }]
```

## The loop

```sh
uniac init      # scaffold uniac.yaml: one service + the deployment instantiating it
uniac plan      # resolve and preview — offline, no auth, no Docker
uniac link      # bind this directory to a remote project (writes .uniac/deploy.json)
uniac deploy    # resolve + materialize + push + register, then watch it settle
uniac status    # what the project is running now
```

**`plan` is the verification loop.** It needs no network, no credentials, and no
Docker daemon; it applies nearly every rule decidable from the manifest alone —
the one-service-per-deployment limit below is the exception, checked only by
`deploy` — and prints the resolved deployable plus its content digest. Run it
after every manifest edit. `deploy` runs the same resolution first, so a
manifest that fails `plan` fails `deploy` for the same reason and with the same
message, before anything is sent anywhere. The two report it differently:
`plan` writes `Error: <message>` to stderr and exits 1; `deploy` reports it in
its final frame on stdout under the `manifest` code, exit 5.

**Identical inputs yield an identical digest.** The deployable is
content-addressed: reordering resources, reindenting YAML, or reordering a
claim list leaves the digest unchanged. A digest that moved means the system
actually changed.

## Ownership

| The platform owns | You own |
|---|---|
| Injecting the resolved `env` at container start | Everything inside the image |
| The private network, addressable by service name | Which port your process binds |
| Public hostnames and allocated TCP ports | Health endpoints, retries, readiness |
| Provisioning and attaching declared durable volumes | The data inside them, and its backups |
| Resolving `${{...}}` values at deploy time | Declaring the references |
| Recreating consumers when a provider's values change | Migrations, data, backups |

The container environment is **exactly** the resolved declared `env` — nothing
is injected beyond it. There is no port declaration on a service: the internal
network is port-transparent, and liveness is observed on the container process,
never by probing a port.

## Constraints to design around

- **One source per service.** A service names exactly one of `image:` (a
  prebuilt OCI reference) or `build:` (a Dockerfile build of your own project
  tree, run by the CLI on your local Docker daemon at deploy time). Declaring
  both, or neither, fails the plan. Schema in `[[uniac-manifest]]`.
- **One service per deployment, today.** A deployment instantiating more than
  one service parses and plans, but `uniac deploy` rejects it. A multi-service
  system is therefore several deployments in one manifest, deployed one at a
  time, wired by cross-deployment references — see `[[uniac-multi-service]]`.
- **Uniac is pre-1.0.** Trust the manifest schema, the final-frame output
  contract, and the exit-code set; treat anything else as liable to move, and
  re-read `uniac <cmd> -h` rather than assuming a flag.

## Where to go next

- `[[uniac-manifest]]` — the full `uniac.yaml` schema, the `${{...}}` reference
  grammar, and every rule that fails at plan time.
- `[[uniac-cli]]` — the command surface and the output contract: the one
  final text frame `deploy` and `status` leave on stdout, typed error codes,
  exit statuses. Read it before parsing any CLI output.
- `[[uniac-multi-service]]` — composing several services into one system:
  cross-service wiring, public exposure, deploy ordering, and what the platform
  does not provide.
