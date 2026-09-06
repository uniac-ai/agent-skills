# Output and errors

## Channels and formats

`deploy` prints one final text report to stdout, containing its execution
record followed by the state it could report. `status` prints the state and,
if its read fails, an error block. Neither command has a JSON mode. Help and
argument-parsing errors go to stderr and leave stdout empty.

Deployment progress uses stderr. By default, a terminal with usable width
gets a live display that clears when the run ends. `UNIAC_PROGRESS=1` streams
plain progress lines; `UNIAC_PROGRESS=0` disables progress. These settings do
not change stdout. `status` has no progress display.

`link` writes its listing, prompt and confirmation to stderr, including when
deployment opens the picker. Other commands write results to stdout and
errors to stderr. A failure to render a status report can also write stderr.

## Plan output

The text preview names the selected deployment and the digest of its generated
description, then shows image work under `Building` and named services under
`Deploying`. Service rows include sources, declared public exposure and
volumes. `--full` adds environment values, the start command and the source
definition's name when it differs from the service name.

`plan --json` emits `{resource, digest, deployable}`. `resource` names the
selected declaration; `deployable` is the generated service description.
Environment and start-command fields are included whether or not `--full`
is supplied. [Resources](../resources/overview.md) defines the generated
description and what its digest identifies.

## Deployment record

The root line names the selected deployment. Its children report `plan`,
`link`, `build`, `push <service>` and `deploy <service>`. They include the
digest of the generated description, project slug, image count, pushed image digest
and observed status when available. Displayed digests are shortened; the
state section contains no image reference or digest.

`✓` marks completion and `✗` marks failure. On failure, the root line carries
an error code and the failed stage includes its retained progress and error
message. A deployment report has no separate `error` block. An interruption
is classified under the stage in flight, and a nonzero exit can still leave
a report and project or service rows.

## State rows

Service state is explained in
[Service observation](../resources/service/overview.md#observed-state), public
addresses in [Networking](../resources/service/networking.md), and durable
storage state in [Volume lifecycle](../resources/volume.md#lifecycle).

| Row | Representation |
|---|---|
| `project` | The linked project's name; deployment falls back to its slug. |
| `platform` | The platform API origin, shown only when it differs from production. |
| `service` | A service name, followed by `v<N>` when a serving version was read. |
| `status` | Reported status, with `(observed/effective)` when replica observation is available. |
| `kind` | Reported service kind, omitted when unavailable. |
| `lifecycle` | Reported serving-deployment phase, omitted when empty or `active`. |
| `deploying` | The in-flight task state and its current step when reported. |
| `replicas` | `<N> requested`, shown when the requested and effective counts differ. |
| `endpoint` | `<type> <address> → :<container-port>`; type and container port are omitted when unavailable. |
| Indented `volume` | `<name> at <mount-path>` on a service. |
| `hold` | A platform hold code. |
| `warning` | A platform warning or a CLI observation/recording warning. |

The endpoint address is the complete address a client uses. A TCP address
includes its allocated public port; the number after `→` is the container
port. Columns align within each block, so their character offsets vary.

Whole-project `status` lists services in name order and adds project volume
blocks after them. Each volume block has its name, `size` in GB and `state`,
including the holding service when available. `deploy` and single-service
`status` show service mounts but do not list volume entities, so they cannot
show retained unattached volumes.

### Partial observations and warnings

A failed service-detail read during whole-project `status` leaves that
service's name and summary status but omits its additional details. A failed
volume read omits the volume section. Either can occur with exit 0. Missing
rows therefore do not establish that the corresponding remote facts are
absent.

When deployment otherwise succeeds but cannot read a service's final state,
it reports `state unread` as a warning. A failed local release-record write produces
`release record not written: <error>`; the remote deployment remains in place.
These warnings do not make the command fail. A name-only service row can also
appear after registration fails and does not establish a running service.

Platform warnings are passed through, including unresolved
[environment references](../resources/service/environment.md).

## Errors and exit codes

A `status` error block contains `error <code>`, a human-readable `message`
and `retryable yes` when reported. Deployment puts the code on the root line
and annotates a retryable failure there. `retryable` means the same operation
may succeed without changes; error messages are explanatory prose.

The following exit codes apply to `deploy` and `status`:

| Exit | Code | Condition |
|---|---|---|
| 0 | — | The command succeeded. |
| 2 | `usage` | Invalid invocation; no deployment attempted and no code printed on stdout. |
| 3 | `auth` | No locally usable credential, or `status` has no project name. |
| 4 | `not_linked` | Binding/platform conflict, or deployment's picker found no projects. |
| 5 | `manifest` | Description validation or deployment-shape failure. |
| 6 | `build` | Docker daemon, image-pull or build failure. |
| 7 | `push` | Image upload failure. |
| 8 | `deploy_failed` | Deployment request/task failure, observation deadline expiry or a refused platform read. |
| 9 | `unreachable` | A platform request was classified as unreachable. |
| 10 | `pending` | Reserved; currently not emitted. |
| 70 | `internal` | Unclassified failure. |

Exit 1 is unassigned for these two commands. Some conditions use a code whose
name does not describe the whole cause:

- `status` without a binding or target override exits 70 when a credential is
  available; without a usable credential it exits 3. A target with no project
  name, including `UNIAC_PROJECT_URL`, exits 3.
- Deployment's project picker can report transport, rejected-credential or
  unanswered-input failures as 70. No projects produces 4.
- Missing build directories or Dockerfiles produce 5 during planning;
  Dockerfile or daemon failures during image work produce 6.
- A rejected platform credential can produce 7 during upload, 8 during a
  deployment request or status read, or 70 during project selection.
- A deployment observation deadline produces 8 while the accepted work
  continues. After a successful first task read, later task-read failures
  also produce 8, including transport failures.
- Status reads and deployment push/request operations classify transport
  errors and HTTP 502, 503, 504, 521, 522, 523 and 530 as unreachable (9).
  Other refused status reads, including 401 and 403, produce 8.

Other commands use 0 for success, 1 for command failure and 2 for invalid
invocation. A description failure produces 1 under `plan` and 5 under
`deploy`. Bare or unknown invocations exit 2; help and `version` exit 0.
