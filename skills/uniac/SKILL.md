---
name: uniac
description: Uniac system composition, uniac.yaml, CLI commands, and platform behavior for developing and operating applications.
---

# Uniac

Uniac is a cloud platform for building and operating systems of connected
services.

## System composition

| Component | Meaning |
|---|---|
| Project | The remote scope containing services and volumes, with a shared private network. |
| Service | An application component named within its project. |
| Volume | Durable storage with its own identity and lifetime, attached to a service or retained unattached. |
| Public endpoint | A service's public address for incoming traffic. |

## Manifest

[Manifest](references/manifest.md) — expressing the system in `uniac.yaml`:
reusable definitions, named service instances, deployment declarations,
fields, references, and local validation.

## CLI and platform

- [CLI](references/cli.md) — command behavior, authentication, project
  selection, and output.
- [Platform](references/platform.md) — how deployed services run, communicate,
  retain data, change, and are removed; what observed state establishes.
