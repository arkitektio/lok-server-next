# Service device code

Registers **one service instance** — a long-running backend that *other* clients
depend on to satisfy their requirements (a database, a Rekuest agent host, a storage
service…). Like the client flow it is human-authorized, but what it produces is a
`ServiceInstance` (with roles, scopes, and advertised aliases) rather than an app
client.

- [When to use](#when-to-use)
- [Why](#why)
- [Protocol](#protocol)
- [Sendable params — machine (REST)](#sendable-params--machine-rest)
- [Sendable params — authorizer (GraphQL)](#sendable-params--authorizer-graphql)
- [Responses](#responses)
- [Code path](#code-path)

## When to use

- You are bringing up a **service** that publishes endpoints (aliases) and defines
  roles/scopes that other clients will resolve against.
- A human should approve which organization the service instance belongs to.
- You want the instance registered once and addressable by other hubs.

Use the [client flow](./client_device_code.md) for an app that *consumes* services;
use the [hub flow](./hub_device_code.md) to register a service
*together with* the clients that use it in a single approval.

## Why

Services are the supply side of the requirement graph: a client's `requirements`
name a `service`, and lok links the client to a matching `ServiceInstance`.
Registering services through their own device-code flow lets the operator who runs
the backend authorize it against the org, publish its aliases, and declare its
roles/scopes — without that operator also being whoever configures the consuming
apps.

This flow introduces the **separate `challenge_code`**: `code` is the human-visible
value shown in the configure URL, while `challenge_code` is the secret the machine
polls with — so the value a person can see is not the value that unlocks the
credential.

## Protocol

1. **Discover** — `GET /.well-known/fakts` (see [discovery](./discovery.md)).
2. **Start** — `POST /f/servicestart/` with the service manifest + aliases ⇒
   `{status: granted, code, challenge}`.
3. **Configure** — show the user the configure URL with `{code}`
   (`/serviceconfigure/<code>`); they pick the org and approve.
4. **Poll** — `POST /f/servicechallenge/` with `{code: <challenge>}` until `granted`,
   then read `token` (the `ServiceInstance` token).

## Endpoints

| Step | Method | Path | URL name |
|---|---|---|---|
| Start | POST | `/f/servicestart/` | `fakts:servicestart` |
| Challenge (poll) | POST | `/f/servicechallenge/` | `fakts:servicechallenge` |

## Sendable params — machine (REST)

### Start — `ServiceDeviceCodeStartRequest`
`POST /f/servicestart/`

| Field | Type | Default | Description |
|---|---|---|---|
| `manifest` | [`ServiceManifest`](./README.md#servicemanifest) | — (required) | The service instance being registered. |
| `staging_aliases` | [`StagingAlias`](./README.md#stagingalias)[] | `[]` | Endpoints the instance advertises. |
| `expiration_time_seconds` | int | `300` | How long the code stays valid. |

### Challenge — `DeviceCodeChallengeRequest`
`POST /f/servicechallenge/`

| Field | Type | Default | Description |
|---|---|---|---|
| `code` | str | — (required) | The `challenge` value returned by start (**not** the human `code`). |

## Sendable params — authorizer (GraphQL)

The configure page looks the code up with `serviceDeviceCodeByCode(code)`.

### `acceptServiceDeviceCode(input: AcceptServiceDeviceCodeInput!) → ManagementServiceInstance`

| Field | Type | Default | Description |
|---|---|---|---|
| `deviceCode` | ID | — (required) | The service device code's **id**. |
| `organization` | ID | — (required) | Organization the `ServiceInstance` is created in. Roles, scopes, and aliases from the manifest are provisioned under it. |

### `declineServiceDeviceCode(input: DeclineServiceDeviceCodeInput!) → ManagementServiceDeviceCode`

| Field | Type | Default | Description |
|---|---|---|---|
| `deviceCode` | ID | — (required) | The service device code's id; marks it denied. |

## Responses

| Endpoint | Success | Non-success |
|---|---|---|
| `/f/servicestart/` | `{status: granted, code, challenge}` | `{status: error, error}` |
| `/f/servicechallenge/` | `{status: granted, token}` | `{status: pending\|denied\|expired}` · `{status: error, error: "Challenge does not exist"}` |

## Code path

- REST: `ServiceStartChallengeView` / `ServiceChallengeView` (`fakts/views.py`);
  polling via `_poll_device_code(device_code, "instance")`.
- Service: `start_service_device_code` (`fakts/services/device_codes.py`).
- Model: `ServiceDeviceCode` (`fakts/models.py`).
- GraphQL: `accept_service_device_code` / `decline_service_device_code`
  (`api/management/mutations/service_device_code.py`); `service_device_code_by_code`
  query and `ManagementServiceDeviceCode` type.
- Frontend: `src/service/ServiceConfigurePage.tsx`, route `/serviceconfigure/:serviceCode`.
