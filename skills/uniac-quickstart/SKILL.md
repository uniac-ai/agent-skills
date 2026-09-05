---
name: uniac-quickstart
description: First deployment of an application on Uniac, connecting its manifest, remote project, directory binding, and public endpoint through a complete example.
---

# Uniac quickstart

Deployment connects a manifest declaration to a remote project. This example
selects the project through a directory binding. Manifest authoring and
project creation are independent.

## Example application

This example starts with an application whose root `Dockerfile` builds a
service listening on `0.0.0.0:8080`. The machine has the Uniac CLI, a running
Docker daemon, and [account access](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli.md#authentication).
It uses a new project named `my-app` and supplies its manifest directly.

The following `uniac.yaml` declares one service and exposes its HTTP port:

```yaml
runtime: yaml
default: main
resources:
  api:
    type: service
    build: .
  main:
    type: deployment
    services:
      api:
        from: api
        public_ports: [{ port: 8080, type: http }]
```

The [manifest reference](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/manifest.md)
defines image sources, additional services, storage, and cross-service references.

## Destination and deployment

With that application and manifest in the current directory:

```sh
uniac plan
uniac project create my-app
uniac link my-app
uniac deploy
uniac status
```

An existing project can be linked by name or slug instead of creating one.
The [project-selection contract](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli.md#project-selection)
also describes selection during deployment and target overrides.

`plan` previews the declaration locally. `deploy` builds the application
image and submits the deployment; `status` reads the resulting project state.
Their [planning and deployment contract](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli.md#planning-and-deployment)
defines requirements and completion behavior.

## Application address

The service's `endpoint` row gives the public URL for exercising the
application. [Platform behavior](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/platform.md)
defines networking and what the reported service state establishes.
