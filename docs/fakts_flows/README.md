# Fakts flows

**Fakts** is how a piece of software (a CLI, a worker, a desktop app, a server, a
machine) obtains its configuration and credentials from lok *without* shipping any
secrets in advance. The software knows only the deployment's base URL; everything
else — client id/secret, tokens, service endpoints, mesh keys — is negotiated at
runtime through one of the **fakts flows** documented here.

Every flow is a small JSON-over-HTTP protocol served under `/f/` (see
`fakts/urls.py`, mounted at `f/` by `lok_server/urls.py`), plus a discovery
document at `/.well-known/fakts`. The interactive flows additionally have a
human-facing side in the SPA (kontrol) where a logged-in user authorizes the
request.

- [1. The shared shape: discover → start → challenge → claim](#1-the-shared-shape)
- [2. Which flow, when](#2-which-flow-when)
- [3. The response envelope](#3-the-response-envelope)
- [4. Two param surfaces: machine vs. authorizer](#4-two-param-surfaces)
- [5. Shared request models](#5-shared-request-models)
- [6. Per-flow references](#6-per-flow-references)

---

## 1. The shared shape

The four **device-code flows** (client, service, hub, mesh) all follow the
same OAuth-device-grant-style choreography:

```
  machine                         lok                         human (kontrol)
    │  GET /.well-known/fakts      │                                │
    │─────────────────────────────▶  discovery: all endpoint URLs   │
    │                              │                                │
    │  POST /f/{x}start/  (manifest)                                │
    │─────────────────────────────▶  stage a device code            │
    │◀───────────────────────────── {code, challenge}               │
    │                              │                                │
    │        (show `code` to a human, who opens the configure URL)  │
    │                              │   ◀── opens /{x}configure/{code}│
    │                              │   ── authorizes (GraphQL accept)│
    │  POST /f/{x}challenge/ (poll)│                                │
    │─────────────────────────────▶  pending … then granted         │
    │◀───────────────────────────── {token | key | …}               │
    │                              │                                │
    │  POST /f/claim/  (token)     │   (client flow only)           │
    │─────────────────────────────▶  rendered configuration         │
```

The two **non-interactive flows** skip the human step: **retrieve** returns a
public app's token directly, and **redeem** exchanges a pre-issued token for a
client. **claim** and **report** are shared steps used after a credential exists.

## 2. Which flow, when

| Flow | Use it to… | Human authorizes? | Credential you get back |
|---|---|---|---|
| [Client device code](./client_device_code.md) | register **one app/client** (a CLI, worker, desktop app) against a user's org | ✅ yes | a `Client` token → `/f/claim/` → full config |
| [Service device code](./service_device_code.md) | register **one service instance** (a long-running backend that others depend on) | ✅ yes | a `ServiceInstance` token |
| [Hub device code](./hub_device_code.md) | stand up a **whole hub** — many instances + clients (+ optional mesh key) in one authorization | ✅ yes | a `Hub` token → `/f/claimhub/` |
| [Mesh device code](./mesh_device_code.md) | let a **machine join the org's mesh** (tailnet) with a configurable machine name | ✅ yes | a single-use ionscale **pre-auth key** + coord URL + machine name |
| [Redeem token](./redeem_token.md) | provision a client **non-interactively** from a pre-shared one-time token (CI, headless installs) | ❌ no | a `Client` token |
| [Retrieve](./retrieve.md) | fetch the token of an app that has a **public** client — no auth at all | ❌ no | a public `Client` token |

Shared steps (not flows on their own): [discovery](./discovery.md) is the entry
point every flow starts from; [claim](./claim.md) turns a token into a rendered
configuration; [report](./report.md) is client-health telemetry.

## 3. The response envelope

Every `/f/` endpoint returns a JSON object whose `status` field is the protocol
signal. Clients branch on it and never on the HTTP status code (endpoints return
`200` even for `error`). The `_poll_device_code` helper and the start/claim views
in `fakts/views.py` produce these:

| `status` | Meaning | Other fields |
|---|---|---|
| `granted` | success | `code` / `challenge` (start) · `token` (challenge, retrieve, redeem) · `config` (claim) · `ionscale_auth_key`, `ionscale_coord_url`, `machine_name` (mesh challenge) |
| `pending` | the human has not authorized yet — keep polling | `message` |
| `denied` | the human declined; the device code is deleted | `message` |
| `expired` | no answer before `expires_at`; the device code is deleted | `message` |
| `error` | malformed request or unknown code/token | `error` or `message` |
| `reported` | report accepted (report endpoint only) | `message` |

Clients should poll the challenge endpoint on a fixed interval and stop on any of
`granted` / `denied` / `expired` / `error`.

## 4. Two param surfaces

For the interactive flows, "sendable params" live on **two different wires**, and
each flow page documents both:

- **What the machine sends** — snake_case JSON to the REST endpoints under `/f/`
  (`requested_client_kind`, `expiration_time_seconds`, `requested_machine_name`, …).
  These are the pydantic request models in `fakts/base_models.py`.
- **What the authorizer sends** — camelCase GraphQL inputs to the management schema
  (`acceptXDeviceCode` / `declineXDeviceCode`), issued by the logged-in user in
  kontrol. This is where the **organization**, and choices like the final machine
  name or `allowIonscale`, are actually set. These are the `@kante.input` classes
  in `api/management/mutations/`.

Field names differ by wire: the REST models are snake_case; the GraphQL inputs are
camelCase (e.g. REST `requested_machine_name` vs. GraphQL `machineName`).

## 5. Shared request models

These nested models recur across flows. They are defined once here; the flow pages
link back rather than repeat them.

### `Manifest`
Describes a client/app. Used by [client device code](./client_device_code.md),
[redeem](./redeem_token.md), [retrieve](./retrieve.md), and inside a hub's
`clients`.

| Field | Type | Default | Description |
|---|---|---|---|
| `identifier` | str | — (required) | Unique app identifier (reverse-domain, e.g. `com.example.app`). |
| `version` | str | — (required) | App version. |
| `title` | str? | `null` | Human display name for the App/Release. |
| `description` | str? | `null` | Human description. |
| `logo` | str? | `null` | URL to a logo; downloaded and validated at start. |
| `scopes` | str[] | `[]` | Requested scopes. |
| `requirements` | [`Requirement`](#requirement)[] | `[]` | Services the client needs to run. |
| `node_id` | str? | `null` | Stable id of the node the client runs on (creates/links a `Device`). |
| `authors` | str[] | `[]` | Maintainers. |
| `keywords` | str[] | `[]` | Discovery tags. |
| `license` | str? | `null` | SPDX id or free text. |
| `homepage` | str? | `null` | Homepage URL. |
| `repo_url` | str? | `null` | Issue-tracker / repo URL. |
| `public_sources` | [`PublicSource`](#publicsource)[]? | `null` | Where the client can be found. |

#### `Requirement`
| Field | Type | Default | Description |
|---|---|---|---|
| `key` | str | — (required) | Requirement key the config fills in. |
| `service` | str | — (required) | Reverse-domain service identifier that satisfies it. |
| `optional` | bool | `false` | If true, the client runs even when unmet (user may decline it). |
| `description` | str? | `null` | Shown to the user when asked to grant it. |

#### `PublicSource`
| Field | Type | Default | Description |
|---|---|---|---|
| `kind` | `"github"` \| `"website"` | — (required) | Source kind. |
| `url` | str | — (required) | Source URL. |

### `ServiceManifest`
Describes a service instance. Used by
[service device code](./service_device_code.md) and inside a hub's
`instances`.

| Field | Type | Default | Description |
|---|---|---|---|
| `identifier` | str | — (required) | Reverse-domain service identifier. |
| `version` | str | — (required) | Service version. |
| `description` | str? | `null` | Human description. |
| `logo` | str? | `null` | Logo URL. |
| `roles` | `{key, description?}`[] | `[]` | Roles this service defines. |
| `scopes` | `{key, description?}`[] | `[]` | Scopes this service defines. |
| `node_id` | str? | `null` | Stable node id (creates/links a `Device`). |
| `instance_id` | str? | `"default"` | Distinguishes multiple instances of the same service. |
| `public_sources` | [`PublicSource`](#publicsource)[]? | `null` | Where the service can be found. |
| `challenge_key` | str? | `null` | Base64 raw Ed25519 public key (32 bytes) for verifying signed alias challenges. |

### `StagingAlias`
An advertised endpoint (URL) for a service instance. Used in the `staging_aliases`
of the service flow and the `aliases` of a hub instance.

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | str | — (required) | Unique alias id. |
| `name` | str? | `null` | Human label. |
| `ssl` | bool | `true` | Whether the alias is served over TLS. |
| `host` | str | — (required) | Host. |
| `port` | int? | `null` | Port. |
| `path` | str? | `null` | Path. |
| `challenge` | str? | `null` | Health/verify URL (200 ⇒ reachable). |
| `kind` | str | `"absolute"` | `absolute` or `relative` (resolved against the linking request). |
| `scope` | `"local"` \| `"network"` \| `"public"` \| `"ionscale"` | `"local"` | Reachability scope. |
| `public` | bool | `false` | If publicly reachable, the coordinator can health-check it directly. |

## 6. Per-flow references

- [Client device code](./client_device_code.md)
- [Service device code](./service_device_code.md)
- [Hub device code](./hub_device_code.md)
- [Mesh device code](./mesh_device_code.md)
- [Redeem token](./redeem_token.md)
- [Retrieve](./retrieve.md)
- [Discovery (`/.well-known/fakts`)](./discovery.md)
- [Claim](./claim.md)
- [Report](./report.md)

> Out of scope: `/.well-known/fakts-challenge` (`lok_server/urls.py`) is a
> placeholder view with no implemented protocol, and `/lok/o/*` OIDC endpoints are
> the standard OpenID flow — see [openid_clients](../openid_clients/README.md), not
> here.
