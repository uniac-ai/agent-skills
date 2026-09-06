# Volume

A volume is durable storage with a project-scoped identity. Its data and
lifetime are independent of the service holding it.

## Required and optional configuration

Volume attachment is optional and available only to singleton services, with
at most one volume per service. An attachment requires:

| Field | Required | Meaning |
|---|---|---|
| `name` | Yes | Local volume name matching `^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$`. |
| `size_gb` | Yes | Number whose value, after truncation toward zero, is at least 1. |
| `mount_path` | Yes | Absolute path other than `/`, with no `.` or `..` segments, repeated slashes, or trailing slash. |

The resulting project-scoped name is `<instance>.<name>`, limited to 127
characters.

At deployment, the platform limits `size_gb` to 4096 and rejects mount paths
at or below `/proc`, `/sys`, and `/dev`, and the path `/etc/resolv.conf`.

## YAML composition example

In [YAML composition](../composition/yaml.md), a volume declaration is a
mapping with `name`, `size_gb`, and `mount_path` inside the service definition's
optional `volumes` list. Omitting `volumes`, setting it to `null`, or using
`[]` declares no volume.

The singleton `cache` service mounts `cache.data` at `/data`. Redis writes its
append-only persistence files there, and the volume retains them across
container replacement.

```yaml
resources:
  cache-code:
    type: singleton
    image: redis:7-alpine
    start_command: redis-server --appendonly yes
    volumes:
      - name: data
        size_gb: 1
        mount_path: /data
  application:
    type: deployment
    services:
      cache:
        from: cache-code
```

In the generated description, the declaration is one `volume` object with
the scoped name, `size_gb`, and `mount_path`.

## Lifecycle

Declaring a new volume name provisions storage. An existing unattached volume
can be attached; a volume held by another service cannot. Redeploying with
the same volume name reuses its data, including when its mount path changes.
Removing the volume declaration on redeploy detaches it; deleting the service
also detaches its volume and preserves its data. Existing volumes cannot be
resized.

A volume's state distinguishes attachment to a service from an unattached
volume whose data is retained. Transitional states include `provisioning`,
`attaching`, `detaching`, and `deleting`.

A fresh volume contains `lost+found`.

Deleting a volume held by a service is rejected. Explicit deletion requires
name confirmation and destroys stored data.
