---
name: uniac
description: Define, deploy, and operate applications on Uniac, including connected services, storage, networking, and CLI operations.
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

## Defining an application

[Application definition](references/application.md) — service definitions,
named instances, deployment declarations, their relationship to a project,
and how `uniac.yaml` describes them.

## CLI and platform

- [Quickstart](https://github.com/uniac-ai/agent-skills/blob/main/skills/uniac-quickstart/SKILL.md)
  — a complete first-deployment example connecting the application,
  manifest, project, and public endpoint.
- [CLI](references/cli.md) — command behavior, authentication, project
  selection, and output.
- [Platform](references/platform.md) — how deployed services run, communicate,
  retain data, change, and are removed; what observed state establishes.
