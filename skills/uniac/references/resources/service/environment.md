# Environment and references

A service definition's `env` is an optional mapping of environment variable
names to plaintext string values. Names match `^[A-Za-z_][A-Za-z0-9_]*$`;
`host` is reserved for the builtin reference.

At deployment, the platform accepts at most 64 declared variables, with
names up to 128 characters and values up to 4096 characters.

The platform resolves declared values at deployment time and injects them
at container start. Other environment defaults are the image's own.

## References

Values can contain references with this grammar:

```text
\$\{\{\s*([a-z0-9][a-z0-9_-]*|self)\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}
```

A reference's scope names a service instance, independently of its
definition name. `${{self.VAR}}` names a variable on the declaring service.
`host` is the only builtin and means the referenced service's internal
hostname.

Chains resolve transitively. Across a chain, `self` remains bound to the
service that declared each value. There is no escape syntax; every `${{`
opener must form a valid reference.

## Resolution

References to `self` must name a builtin or a declared variable. Composition
of a deployment checks references to other instances in that deployment
against their declared variables and builtins, and rejects reference cycles.

A name outside the selected deployment passes through for remote resolution,
even if another deployment in the file defines it. Remote references resolve
within the target project.

An unresolved reference omits the affected variable from Uniac's injected
values and produces a warning; it does not fail the deployment. After a
successful deployment, the platform re-resolves the project's other services
and recreates those whose injected values changed. Uniac provides no
dependency ordering or readiness coordination.
