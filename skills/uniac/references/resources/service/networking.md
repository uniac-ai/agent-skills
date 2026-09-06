# Networking and endpoints

Services are addressable as `<instance>.internal` within their project.
Internal communication does not require port declarations. Without public
exposure, a service is directly reachable only within its project.

The application chooses its listen port. Uniac does not automatically supply
a `PORT` variable or configure the application to match a public endpoint.

## Public endpoints

A public endpoint forwards incoming traffic to the application's listen port.

| Type | Allocated endpoint |
|---|---|
| `http` | An address at `https://<hostname>` on the shared HTTP edge, routing to the application's specified port. |
| `tcp` | A public hostname and port, forwarding raw TCP to the application's specified port. The public port is allocated independently of the listen port. |

## Required and optional configuration

Public exposure is optional. Each requested endpoint specifies:

| Field | Required | Meaning |
|---|---|---|
| `port` | Yes | The application's listen port, as a number truncated toward zero. |
| `type` | Yes | `http` or `tcp`. |

The platform accepts ports 1–65535 and at most one exposure of each type per
service. These limits are enforced during deployment, beyond local schema
validation.

## YAML composition example

In [YAML composition](../../composition/yaml.md),
`services.<instance>.public_ports` is an optional list of mappings, each with
`port` and `type`. Its presence has three meanings on deployment:

| Value | Result |
|---|---|
| Omitted or `null` | Keeps the service's existing public exposure. |
| `[]` | Removes all public exposure. |
| Nonempty list | Replaces public exposure with exactly this list. |

This service's port 8080 receives traffic through both an HTTPS endpoint and
a separately allocated raw TCP endpoint.

```yaml
resources:
  echo:
    type: service
    image: mendhak/http-https-echo:31
  application:
    type: deployment
    services:
      web:
        from: echo
        public_ports:
          - port: 8080
            type: http
          - port: 8080
            type: tcp
```
