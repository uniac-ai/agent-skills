# Environment and references

Environment variables provide runtime configuration to a service's containers.
Their values can refer to the service's own configuration or to another
service in the same project. The platform resolves declared values at
deployment time and injects them at container start. Other environment
defaults are the image's own.

## Required and optional configuration

Environment configuration is optional. Each declared variable requires:

| Information | Required | Meaning |
|---|---|---|
| Name | Yes | The environment variable's name. |
| Value | Yes | Plaintext string, optionally containing references. |

Variable names match `^[A-Za-z_][A-Za-z0-9_]*$`; `host` is reserved for the
builtin reference. At deployment, the platform accepts at most 64 declared
variables, with names up to 128 characters and values up to 4096 characters.

## References

A reference's scope names a service instance, independently of its
definition name. `${{self.VAR}}` names a variable on the declaring service.
`host` is the only builtin and means the referenced service's internal
hostname.

References have this grammar:

```text
\$\{\{\s*([a-z0-9][a-z0-9_-]*|self)\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}
```

Chains resolve transitively. Across a chain, `self` remains bound to the
service that declared each value. There is no escape syntax; every `${{`
opener must form a valid reference.

## YAML composition example

In [YAML composition](../../composition/yaml.md), the service definition's
optional `env` field maps variable names to string values.

The `web` service receives the URL declared by `api`. That URL uses `api`'s
own internal hostname; the definition names remain local labels.

```yaml
resources:
  api-code:
    type: service
    image: mendhak/http-https-echo:31
    env:
      URL: "http://${{self.host}}:8080"
  web-code:
    type: service
    image: mendhak/http-https-echo:31
    env:
      API_URL: "${{api.URL}}"
  api-release:
    type: deployment
    services:
      api:
        from: api-code
  web-release:
    type: deployment
    services:
      web:
        from: web-code
```

## Resolution

References to `self` must name a builtin or a declared variable. Composition
of a deployment checks references to other instances in that deployment
against their declared variables and builtins, and rejects reference cycles.

A name outside the selected deployment passes through for remote resolution,
even if another deployment in the file defines it. Remote references resolve
within the target project.

Remote references use services with a serving deployment. For those services,
`host` supplies the internal hostname without requiring a running replica;
a custom-variable reference requires that variable in the service's resolved
environment.

An unresolved reference omits the affected variable from Uniac's injected
values and produces a warning; it does not fail the deployment. After a
successful deployment, the platform re-resolves the project's other services
and recreates those whose injected values changed. Uniac provides no
dependency ordering or readiness coordination.
