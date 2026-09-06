# Volume

A volume is durable storage with a project-scoped identity. Its data and
lifetime are independent of the service holding it.

## Declaration

A service definition may declare at most one entry in `volumes`; a nonempty
list is allowed only with `type: stateful`. Omitting `volumes`, setting it to
`null`, or using `[]` declares no volume.

Each entry is a mapping with three required fields:

| Field | Meaning |
|---|---|
| `name` | Local volume name matching `^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$`. |
| `size_gb` | YAML number whose value, after truncation toward zero, is at least 1. |
| `mount_path` | Normalized absolute path other than `/`. |

The resulting project-scoped name is `<instance>.<name>`, limited to 127
characters. In the generated description, the declaration is one `volume`
object with that scoped name, `size_gb`, and `mount_path`.

At deployment, the platform limits `size_gb` to 4096 and rejects mount paths
at or below `/proc`, `/sys`, and `/dev`, and the path `/etc/resolv.conf`.

## Lifecycle

Declaring a new volume name provisions storage. An existing unattached volume
can be attached; a volume held by another service cannot. Redeploying with
the same volume name reuses its data, including when its mount path changes.
Removing the volume declaration on redeploy detaches it; deleting the service
also detaches its volume and preserves its data. Existing volumes cannot be
resized.

A volume's state distinguishes attachment to a service from an unattached
volume whose data is retained. Transitional states include `provisioning`,
`attaching`, `detaching`, and `deleting`. The volume has its own provisioned
size; a service's mount records which volume it holds and its mount path.

A fresh volume contains `lost+found`.

Deleting a volume held by a service is rejected. Explicit deletion requires
name confirmation and destroys stored data.
