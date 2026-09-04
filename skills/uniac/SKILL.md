---
name: uniac
description: Build, deploy, and operate applications on Uniac. Use for uniac.yaml, the uniac CLI, or applications targeting Uniac.
---

# Uniac

Uniac runs container images in remote projects. `uniac.yaml` describes the
application; the CLI builds or pulls its images and uploads them to the
project. Containers require no Uniac library or runtime package.

## Model

| Concept | Meaning |
|---|---|
| Service definition | A reusable workload description: image or Dockerfile build, environment, and optional start command. `type: stateful` permits durable storage and limits each deployed service to one running container. |
| Service instance | A named use of a definition. Its name identifies the running service, environment references, and its storage. |
| Deployment | A manifest resource that names service instances and their public exposure. The CLI currently deploys one service per deployment. |
| Project | A remote collection of services sharing a private network. Several deployments can contribute services to the same project. |

Definitions and deployments are local descriptions. Removing a resource
from YAML does not delete its running service or volume in the remote project.

## References

Read the reference for the concern being worked on:

- [Manifest](references/manifest.md) — authoring or inspecting `uniac.yaml`:
  fields, build paths, environment references, and local validation.
- [CLI](references/cli.md) — invoking commands or interpreting results:
  prerequisites, authentication, project selection, output, and exit codes.
- [Platform](references/platform.md) — designing, operating, or diagnosing
  a running application: networking, runtime behavior, storage, and removal.
