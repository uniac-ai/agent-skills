# Concepts

Uniac is a cloud platform for building and operating systems of connected
services.

| Concept | Meaning |
|---|---|
| [Project](project.md) | The remote scope containing services and volumes, with a shared private network. |
| [Service](resources/service/overview.md) | A named application component running within a project. |
| [Volume](resources/volume.md) | Durable storage with its own identity and lifetime, attached to a service or retained unattached. |
| [Public endpoint](resources/service/networking.md) | A service's public address for incoming traffic. |

[Resources](resources/overview.md) describe the application: reusable service
definitions and deployment declarations that give their instances names.
The application description and the remote project are separate; the same
description can target different projects.
