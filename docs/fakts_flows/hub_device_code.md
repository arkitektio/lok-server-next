# Hub device code

Stands up an **entire hub** in a single authorization: a `Hub` bundles many
service instances *and* client apps (and, optionally, a mesh pre-auth key) that are
created together and share one token. Instead of running the client and service
flows N times, an operator describes the whole topology once and a human approves it
in one click.

- [When to use](#when-to-use)
- [Why](#why)
- [Protocol](#protocol)
- [Sendable params — machine (REST)](#sendable-params--machine-rest)
- [Sendable params — authorizer (GraphQL)](#sendable-params--authorizer-graphql)
- [Responses](#responses)
- [Code path](#code-path)

## When to use

- You are deploying a **hub / stack**: several services and the clients that use
  them, meant to come up as a unit.
- You want a single `Hub` token that renders the whole configuration (see
  [claim](./claim.md), hub variant).
- Optionally, the hub's servers should join the org mesh — set `request_auth_key`
  and the accept step mints a hub-scoped ionscale key.

For a single app use the [client flow](./client_device_code.md); for a single
service the [service flow](./service_device_code.md); to add just a machine to the
mesh (no hub) use the [mesh flow](./mesh_device_code.md).

## Why

A hub is a topology, not a single credential. Provisioning it piecemeal is
error-prone and forces the authorizing user to approve many disconnected requests.
The hub manifest captures the instances, the clients, their aliases, and
whether the hub needs a mesh key; `accept_hub_device_code` materializes all
of it under one organization atomically and, when asked, attaches a mesh key via the
org's existing mesh (read-only — it will not silently create a tailnet).

Like the service flow, it uses a **separate `challenge_code`** for polling.

## Protocol

1. **Discover** — `GET /.well-known/fakts` (see [discovery](./discovery.md)).
2. **Start** — `POST /f/hubstart/` with the hub manifest ⇒
   `{status: granted, code, challenge}`.
3. **Configure** — show the user the configure URL with `{code}`
   (`/hubconfigure/<code>`); they pick the org and approve.
4. **Poll** — `POST /f/hubchallenge/` with `{code: <challenge>}` until
   `granted`, then read `token` (the `Hub` token).
5. **Claim** — `POST /f/claimhub/` with the token for the rendered server
   configuration (see [claim](./claim.md)).

## Endpoints

| Step | Method | Path | URL name |
|---|---|---|---|
| Start | POST | `/f/hubstart/` | `fakts:hubstart` |
| Challenge (poll) | POST | `/f/hubchallenge/` | `fakts:hubchallenge` |
| Claim | POST | `/f/claimhub/` | `fakts:hubclaim` |

## Sendable params — machine (REST)

### Start — `HubStartRequest`
`POST /f/hubstart/`

| Field | Type | Default | Description |
|---|---|---|---|
| `hub` | [`HubManifest`](#hubmanifest) | — (required) | The hub topology to provision. |
| `expiration_time_seconds` | int | `600` | How long the code stays valid. |

#### `HubManifest`
| Field | Type | Default | Description |
|---|---|---|---|
| `identifier` | str | — (required) | Unique hub id **within the organization**. |
| `description` | str? | `null` | Human description. |
| `logo` | str? | `null` | Logo URL. |
| `instances` | [`InstanceRequest`](#instancerequest)[] | `[]` | Service instances to create. |
| `clients` | [`ClientRequest`](#clientrequest)[] | `[]` | Client apps to create. |
| `request_auth_key` | bool | `false` | If true (and the authorizer allows), mint a hub-scoped mesh pre-auth key. |

#### `InstanceRequest`
| Field | Type | Default | Description |
|---|---|---|---|
| `identifier` | str | — (required) | Request identifier. |
| `description` | str? | `null` | Human description. |
| `manifest` | [`ServiceManifest`](./README.md#servicemanifest) | — (required) | The service instance. |
| `aliases` | [`StagingAlias`](./README.md#stagingalias)[] | `[]` | Endpoints the instance advertises. |

#### `ClientRequest`
| Field | Type | Default | Description |
|---|---|---|---|
| `identifier` | str | — (required) | Request identifier. |
| `description` | str? | `null` | Human description. |
| `manifest` | [`Manifest`](./README.md#manifest) | — (required) | The client app. |

### Challenge — `DeviceCodeChallengeRequest`
`POST /f/hubchallenge/`

| Field | Type | Default | Description |
|---|---|---|---|
| `code` | str | — (required) | The `challenge` value returned by start. |

### Claim — `ServerClaimRequest`
See [claim](./claim.md#hub-claim). `{ token }`.

## Sendable params — authorizer (GraphQL)

The configure page looks the code up with `hubDeviceCodeByCode(code)`.

### `acceptHubDeviceCode(input: AcceptHubDeviceCodeInput!) → ManagementHub`

| Field | Type | Default | Description |
|---|---|---|---|
| `deviceCode` | ID | — (required) | The hub device code's **id**. |
| `organization` | ID | — (required) | Organization the hub is created in. |
| `allowIonscale` | bool | `true` | Gate for minting the mesh key: a key is created only when this is `true` **and** the manifest's `request_auth_key` is set **and** the org has a mesh. |

### `declineHubDeviceCode(input: DeclineHubDeviceCodeInput!) → ManagementHubDeviceCode`

| Field | Type | Default | Description |
|---|---|---|---|
| `deviceCode` | ID | — (required) | The hub device code's id; marks it denied. |

## Responses

| Endpoint | Success | Non-success |
|---|---|---|
| `/f/hubstart/` | `{status: granted, code, challenge}` | `{status: error, error}` |
| `/f/hubchallenge/` | `{status: granted, token}` | `{status: pending\|denied\|expired}` · `{status: error, error: "Challenge does not exist"}` |
| `/f/claimhub/` | `{status: granted, config}` | `{status: error, message}` |

## Code path

- REST: `HubStartChallengeView` / `HubChallengeView` /
  `ClaimHubView` (`fakts/views.py`); polling via
  `_poll_device_code(device_code, "hub")`.
- Service: `start_hub_device_code` (`fakts/services/device_codes.py`),
  `create_hub_auth_key` (`fakts/services/hubs.py`).
- Model: `HubDeviceCode` (`fakts/models.py`).
- GraphQL: `accept_hub_device_code` / `decline_hub_device_code`
  (`api/management/mutations/hub_device_code.py`);
  `hub_device_code_by_code` query and `ManagementHubDeviceCode` type.
- Frontend: `src/hub/HubConfigurePage.tsx`, route
  `/hubconfigure/:hubCode`.
