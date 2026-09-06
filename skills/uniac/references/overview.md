# How Uniac works

Uniac is a cloud platform for building and operating distributed applications.
It brings together services, private communication, public endpoints, and
persistent storage so an application can run as connected components.

## Accounts, projects, and applications

An account can own multiple projects. Each project is a deployment destination
with its own services, volumes, and private network. Project names are unique
within an account; the platform also assigns each project a slug.

An application is made up of resources that run together in a target project.
Its description is separate from that destination: the same application can
be deployed to different projects, and a project's services can be added or
updated independently.

## Services and communication

Services represent the application's microservices. Each service has an
identity within its project, which other services address on the private
network. The identity stays the same as the running copies of the service,
its **replicas**, change. A public endpoint allows clients outside the project
to reach a service.

A stateless service can run multiple interchangeable replicas behind that
identity. Connections may reach different replicas; a replica's memory and
local files belong to that replica. Services that need shared or persistent
state communicate with the component holding it.

## Singleton services and volumes

A singleton service permits at most one running replica per service in its
project. During replacement, the previous replica stops before its successor
starts. Both service kinds retain their network identity across replacement.

A volume supplies durable storage that survives replacement of the container
using it. A singleton service can attach a volume; data written to its mount
survives replica replacement. Singleton execution alone does not preserve
memory or container-local files. The volume has its own identity and lifetime
within the project. Detaching it or deleting its service retains the data.

For example, an application can have a stateless API and a singleton database.
The API's replicas reach the database through its service identity; the
database's replica stores persistent data on its volume. Public clients need
an endpoint for the API, while the database can remain private.

## Project lifetime

The project retains live state independently of the application description.
Removing a service from that description does not delete the running service.

The [dashboard](https://uniac.ai) opens an account's projects and their
services without a local application description. A project's **Settings**
offers **Delete project**, confirmed by typing its name. This removes its
services and endpoints. Volume data is retained, but those volumes can no
longer be inspected or managed through the deleted project.

## Describing the application

A **composition** describes the resources making up an application and how
they connect. Reusable definitions describe service configuration; named
instances give the resulting services their identities in the target project.
Deployment declarations select the instances to create or update.

[Composition in YAML](composition/yaml.md) introduces the description file
and combines these parts in an example. Detailed configuration and lifecycle information
is available for [Service](resources/service.md) and
[Volume](resources/volume.md).
