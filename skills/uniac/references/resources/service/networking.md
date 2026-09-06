# Networking and endpoints

Services are addressable as `<instance>.internal` within their project.
Internal communication does not require port declarations. Without public
exposure, a service is directly reachable only within its project.

The application chooses its listen port. Uniac does not automatically supply
a `PORT` variable or configure the application to match a public endpoint.

## Public endpoints

`services.<instance>.public_ports` in a deployment declaration specifies
public exposure for that instance. Each entry is a mapping with two required
fields:

| Field | Meaning |
|---|---|
| `port` | The application's listen port, as a YAML number truncated toward zero. |
| `type` | `http` or `tcp`. |

The list has three meanings on deployment:

| Value | Result |
|---|---|
| Omitted or `null` | Keeps the service's existing public exposure. |
| `[]` | Removes all public exposure. |
| Nonempty list | Replaces public exposure with exactly this list. |

The platform accepts ports 1–65535 and at most one exposure of each type per
service. These limits are enforced during deployment, beyond local schema
validation.

| Type | Allocated endpoint |
|---|---|
| `http` | An address at `https://<hostname>` on the shared HTTP edge, routing to the application's specified port. |
| `tcp` | A public hostname and port, forwarding raw TCP to the application's specified port. The public port is allocated independently of the listen port. |
