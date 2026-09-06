# Project

A project belongs to an account. Its name is unique within that account
and matches `^[a-z][a-z0-9-]{0,62}$`; the platform also assigns a project
slug. Its [services](resources/service/overview.md)
and [volumes](resources/volume.md) have identities within the project.
Services share a [private network](resources/service/networking.md).

The project retains live state independently of the local application
description. Applying a deployment does not remove services absent from
`uniac.yaml`.

## Dashboard

The [dashboard](https://uniac.ai) reads projects directly, with no local
manifest or directory binding. Signed in with the project's account,
**Projects** opens the project's services.

The project's **Settings** offers **Delete project**, confirmed by typing
its name; this removes the project's services and endpoints.
Volume data is retained, but those volumes can no longer be inspected or
managed through the deleted project.
