---
name: uniac
description: Define, deploy, and operate applications on Uniac, including connected services, storage, networking, and CLI operations.
---

# Uniac

## Reading path

The introduction develops the system model before its description format and
operation:

1. [How Uniac works](references/overview.md) — accounts and projects,
   applications, service identities, replicas, and persistent state.
2. [Composition in YAML](references/composition/yaml.md) — `uniac.yaml`, resource
   definitions, named instances, and a connected application example.
3. [Uniac CLI](references/cli/overview.md) — deploying that composition to a
   project, selecting the destination, and observing the result.

## Resource details

| Topic | Detail |
|---|---|
| [Service](references/resources/service/overview.md) | Configuration fields, sources, replicas, deployment versions, and a YAML example. |
| [Volume](references/resources/volume.md) | Required fields, persistence, attachment, deletion, and a YAML example. |
| [Networking and endpoints](references/resources/service/networking.md) | Private addresses and public exposure. |
| [Environment and references](references/resources/service/environment.md) | Values, reference scope, resolution, and updates. |

## CLI details

[Authentication](references/cli/authentication.md) covers sign-in and credential
lifetime. [Output and errors](references/cli/output.md) covers reports, partial
observations, and exit codes.

## Example

[Quickstart](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac-quickstart/SKILL.md)
connects an application description, a remote project, and a public endpoint
in one first-deployment example.
