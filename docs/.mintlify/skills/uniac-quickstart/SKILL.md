---
name: uniac-quickstart
description: First deployment of an application on Uniac through a complete example of its description, remote project, project binding, and public endpoint.
---

# Uniac quickstart

## Example application

This example starts with an application whose root `Dockerfile` builds a
service listening on `0.0.0.0:8080`. The machine has the Uniac CLI, a running
Docker daemon, and [account access](https://docs.uniac.ai/cli/authentication.md).
It uses a new project named `my-app`, supplies its application description
directly, and binds the local project to that remote destination.

The following `uniac.yaml` declares one service and exposes its HTTP port:

```yaml
runtime: yaml
resources:
  api_definition:
    type: service
    build: .
  main:
    type: deployment
    services:
      api:
        from: api_definition
        public_ports: [{ port: 8080, type: http }]
```

The `main` deployment instantiates `api_definition` as the service `api`.
[Composition in YAML](https://docs.uniac.ai/composition/yaml.md)
describes the file format and instantiation rules.

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
The [project-selection contract](https://docs.uniac.ai/cli/overview.md#project-selection)
also describes selection during deployment and target overrides.

The [CLI reference](https://docs.uniac.ai/cli/overview.md#planning-and-deployment)
defines these commands' requirements and completion behavior.

## Application address

The HTTP address in the service's `endpoint` row is this application's
public URL. [Output and errors](https://docs.uniac.ai/cli/output.md)
describes the report; [Service](https://docs.uniac.ai/resources/service.md)
defines what the observed state establishes.
