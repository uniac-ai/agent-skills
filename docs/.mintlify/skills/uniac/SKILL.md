---
name: uniac
description: Define, deploy, and operate applications on Uniac, including connected services, storage, networking, and CLI operations.
---

# Uniac

## Reading path

The introduction develops the system model before its description format and
operation:

1. [How Uniac works](https://docs.uniac.ai/index.md) — accounts and projects,
   applications, service identities, replicas, and persistent state.
2. [Composition in YAML](https://docs.uniac.ai/composition/yaml.md) — `uniac.yaml`,
   workspaces, package scopes, named instances, and a connected application example.
3. [Uniac CLI](https://docs.uniac.ai/cli/overview.md) — deploying that composition to a
   project, selecting the destination, and observing the result.

## Resource details

| Topic | Detail |
|---|---|
| [Service](https://docs.uniac.ai/resources/service.md) | Configuration, sources, networking, environment references, replicas, deployment versions, and a YAML example. |
| [Volume](https://docs.uniac.ai/resources/volume.md) | Required fields, persistence, attachment, deletion, and a YAML example. |

## CLI details

[Authentication](https://docs.uniac.ai/cli/authentication.md) covers sign-in and credential
lifetime. [Output and errors](https://docs.uniac.ai/cli/output.md) covers reports, partial
observations, and exit codes.

## Example

[Quickstart](https://docs.uniac.ai/quickstart.md)
connects an application description, a remote project, and a public endpoint
in one first-deployment example.
