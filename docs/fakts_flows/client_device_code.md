# Client device code ("device configure")

The canonical fakts flow: a piece of software that is **one app / one client** — a
CLI, a headless worker, a desktop app — asks to be registered against a user's
organization. The software prints a short code; a human opens the configure page,
picks which hub (hub) to attach it to, and approves; the software polls
until it receives its client token, then claims its full configuration.

- [When to use](#when-to-use)
- [Why](#why)
- [Protocol](#protocol)
- [Sendable params — machine (REST)](#sendable-params--machine-rest)
- [Sendable params — authorizer (GraphQL)](#sendable-params--authorizer-graphql)
- [Responses](#responses)
- [Code path](#code-path)

## When to use

- You are distributing an **application** (not a shared service) that each user runs
  and that needs its own credential bound to *their* account and org.
- A human is present to approve the registration in a browser.
- You want the app to end up with a `client_id`/`client_secret` and a rendered
  configuration (endpoints, auth, requirement mappings).

Use a different flow when: the thing is a shared backend other apps depend on
([service](./service_device_code.md)); you are provisioning many things at once
([hub](./hub_device_code.md)); no human is present
([redeem](./redeem_token.md)); or the app is public and needs no per-user binding
([retrieve](./retrieve.md)).

## Why

Device-grant keeps secrets off the wire the machine can't protect: the app never
holds a client secret until *after* a signed-in human has explicitly approved it
against a specific organization. The human-visible `code` is deliberately short and
low-entropy — it only *names* the pending request in the UI; possession of it grants
nothing, because the app polls with the *same* `code` and the credential is only
released once the DB row has a `client` attached.

## Protocol

1. **Discover** — `GET /.well-known/fakts` for the `device_code_start`,
   `challenge_url`, `configure`, and `claim` URLs (see [discovery](./discovery.md)).
2. **Start** — `POST /f/start/` with the app manifest ⇒ `{status: granted, code}`.
3. **Configure** — show the user `configure` with `{code}` substituted (e.g.
   `/configure/<code>`). They review the app and choose a hub, then approve.
4. **Poll** — `POST /f/challenge/` with `{code}` until `granted`, then read `token`.
5. **Claim** — `POST /f/claim/` with the `token` for the rendered config (see
   [claim](./claim.md)).

Unlike the service/hub/mesh flows, the client flow has **no separate
`challenge_code`**: the human-visible `code` is also the polling secret.

## Endpoints

| Step | Method | Path | URL name |
|---|---|---|---|
| Start | POST | `/f/start/` | `fakts:start` |
| Challenge (poll) | POST | `/f/challenge/` | `fakts:challenge` |
| Claim | POST | `/f/claim/` | `fakts:claim` |

## Sendable params — machine (REST)

### Start — `DeviceCodeStartRequest`
`POST /f/start/`

| Field | Type | Default | Description |
|---|---|---|---|
| `manifest` | [`Manifest`](./README.md#manifest) | — (required) | The app being registered. |
| `expiration_time_seconds` | int | `300` | How long the code stays valid before it expires. |
| `redirect_uris` | str[] | `[]` | OAuth redirect URIs for the resulting client. |
| `requested_client_kind` | enum | `"development"` | Client auth kind: `development` \| `website` \| `desktop`. |
| `requested_client_role` | enum | `"interface"` | Operational role: `interface` (human-driven) \| `agent` (unattended). |
| `request_public` | bool | `false` | Ask for the client to be marked public (retrievable by others). |
| `supported_layers` | str[] | `["web"]` | Requested network layers. **Note:** accepted but not currently consumed — `start_device_code` does not persist it onto the device code. |

### Challenge — `DeviceCodeChallengeRequest`
`POST /f/challenge/`

| Field | Type | Default | Description |
|---|---|---|---|
| `code` | str | — (required) | The `code` returned by start. |

### Claim — `ClaimRequest`
See [claim](./claim.md#sendable-params). `{ token, secure=false }`.

## Sendable params — authorizer (GraphQL)

Issued by the signed-in user in kontrol against the management schema. The configure
page first looks the code up with the `deviceCodeByCode(code)` query.

### `acceptDeviceCode(input: AcceptDeviceCodeInput!) → ManagementClient`

| Field | Type | Default | Description |
|---|---|---|---|
| `deviceCode` | ID | — (required) | The device code's **id** (from `deviceCodeByCode`). |
| `hub` | ID | — (required) | The hub/hub to attach the client to; its `organization` becomes the client's org. |
| `deviceName` | str? | `null` | Name for a newly created device (ignored if the device already exists). |
| `declinedRequirements` | str[] | `[]` | Keys of **optional** requirements the user declined. |

### `declineDeviceCode(input: DeclineDeviceCodeInput!) → ManagementDeviceCode`

| Field | Type | Default | Description |
|---|---|---|---|
| `deviceCode` | ID | — (required) | The device code's id; marks it denied. |

## Responses

| Endpoint | Success | Non-success |
|---|---|---|
| `/f/start/` | `{status: granted, code}` | `{status: error, error}` (e.g. logo download failed) |
| `/f/challenge/` | `{status: granted, token}` | `{status: pending\|denied\|expired}` · `{status: error, error: "Challenge does not exist"}` |
| `/f/claim/` | `{status: granted, config}` | `{status: error, message}` |

## Code path

- REST: `StartChallengeView` / `ChallengeView` / `ClaimView` (`fakts/views.py`);
  polling via `_poll_device_code(device_code, "client")`.
- Service: `start_device_code`, `validate_device_code` (`fakts/services/device_codes.py`),
  `create_client` (`fakts/services/clients.py`).
- Model: `DeviceCode` (`fakts/models.py`).
- GraphQL: `accept_device_code` / `decline_device_code`
  (`api/management/mutations/device_code.py`); `device_code_by_code` query and
  `ManagementDeviceCode` type (`api/management/schema.py`, `types.py`).
- Frontend: `src/device/ConfigurePage.tsx` (kontrol), route `/configure/:deviceCode`.
