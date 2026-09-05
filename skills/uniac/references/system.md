# System model

| Component | Meaning |
|---|---|
| Project | The remote scope containing services and volumes, with a shared private network. Separate projects provide separate environments. |
| Service | A named application component, such as an API, worker, or database. Its name identifies it within the project. |
| Volume | Durable storage with its own identity and lifetime, attached to a service or retained unattached. |
| Public endpoint | An externally reachable address that routes traffic to a service. It belongs to that service. |

Services can refer to other services' configuration values and internal
hostnames. These references, network access, and volume attachments express
relationships between components.

The [manifest](manifest.md) defines services and these relationships. Its
declarations and the project's live state are distinct: several declarations
can contribute services to one project, and deleting a declaration does not
delete its deployed service or retained data.
