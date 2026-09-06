---
name: uniac-quickstart
description: First deployment of an application on Uniac through a complete example of its description, remote project, directory binding, and public endpoint.
---

# Uniac quickstart

## Example application

This example starts with an application whose root `Dockerfile` builds a
service listening on `0.0.0.0:8080`. The machine has the Uniac CLI, a running
Docker daemon, and [account access](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli/authentication.md).
It uses a new project named `my-app`, supplies its application description
directly, and selects the project through a directory binding.

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

[Composition in YAML](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/composition/yaml.md)
defines the relationship between `api`, its definition, and `main`.

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
The [project-selection contract](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli/overview.md#project-selection)
also describes selection during deployment and target overrides.

The [CLI reference](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli/overview.md#planning-and-deployment)
defines these commands' requirements and completion behavior.

## Application address

The HTTP address in the service's `endpoint` row is this application's
public URL. [Output and errors](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/cli/output.md)
describes the report; [Service](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac/references/resources/service/overview.md)
defines what the observed state establishes.
