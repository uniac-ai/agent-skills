---
name: uniac
description: Define, deploy, and operate applications on Uniac, including connected services, storage, networking, and CLI operations.
---

# Uniac

[Concepts](references/concepts.md) introduces Uniac's purpose, system
composition, and the relationship between an application description and
running resources.

[Project](references/project.md) defines the remote destination, identity,
scope, and lifecycle.

## Resources

- [Overview and composition](references/resources/overview.md) — definitions,
  service instances, deployment declarations, and their representation in `uniac.yaml`.
- [Service](references/resources/service/overview.md) — sources, configuration,
  service types, deployment versions, replicas, and lifecycle.
- [Networking and endpoints](references/resources/service/networking.md) —
  private addressing and public exposure.
- [Environment and references](references/resources/service/environment.md) —
  values, reference scope, resolution, and updates.
- [Volume](references/resources/volume.md) — definition, attachment,
  persistence, reuse, and deletion.

## Uniac CLI

- [Overview and commands](references/cli/overview.md) — invocation, prerequisites,
  project selection, planning, deployment, and observation.
- [Authentication](references/cli/authentication.md) — sign-in, credentials,
  platform selection, and session lifetime.
- [Output and errors](references/cli/output.md) — reports, partial results,
  streams, and exit codes.

## Example

[Quickstart](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac-quickstart/SKILL.md)
connects an application description, a remote project, and a public endpoint
in one first-deployment example.
