# Retrieve

The simplest flow: fetch the token of an app that already has a **public** client —
**no authorization and no human at all**. If a `Release` has a client marked
`public`, any caller that knows the app's identifier and version can retrieve that
client's token.

- [When to use](#when-to-use)
- [Why](#why)
- [Protocol](#protocol)
- [Sendable params](#sendable-params)
- [Responses](#responses)
- [Code path](#code-path)

## When to use

- The app is genuinely **public** — a shared, read-only-ish client that isn't bound
  to a specific user or org and whose token grants only what a public client may do.
- You want zero-friction bootstrap for an open app (no device code, no pre-shared
  secret).

Do **not** use this for anything user- or org-scoped: retrieve deliberately hands
back a shared credential. For per-user binding use a
[device-code flow](./client_device_code.md); for headless-but-private installs use
[redeem](./redeem_token.md).

## Why

Some apps are meant to be openly usable and don't need a per-user credential. For
those, requiring a device-code dance is pure friction. Retrieve exists so a public
app can obtain its (public) client token from just its manifest. It is intentionally
narrow: it only ever returns a client that was explicitly flagged `public`, and it
errors otherwise — so making a client retrievable is an explicit opt-in
(`request_public` on the [client flow](./client_device_code.md), or a client marked
public by an operator).

## Protocol

1. **Discover** — `GET /.well-known/fakts` (see [discovery](./discovery.md)).
2. **Retrieve** — `POST /f/retrieve/` with the app manifest ⇒ `{status: granted,
   token}` if the release has a public client. Claim it as usual (see
   [claim](./claim.md)).

## Endpoints

| Step | Method | Path | URL name |
|---|---|---|---|
| Retrieve | POST | `/f/retrieve/` | `fakts:retrieve` |

## Sendable params

### `RetrieveRequest`
`POST /f/retrieve/`

| Field | Type | Default | Description |
|---|---|---|---|
| `manifest` | [`Manifest`](./README.md#manifest) | — (required) | Identifies the app (`identifier` + `version`) whose public client to return. |
| `redirect_uris` | str[] | `[]` | Redirect URIs (reserved; predefined values apply to public clients). |

## Responses

| Endpoint | Success | Non-success |
|---|---|---|
| `/f/retrieve/` | `{status: granted, token}` | `{status: error, …}` — no such app/release, or no public client for that release. |

## Code path

- REST: `RetrieveView` (`fakts/views.py`) — looks up `App` + `Release`, returns the
  first `client` with `public=True`.
- Model: `Client.public` (`fakts/models.py`).
- Related: `request_public` on `DeviceCodeStartRequest` is how a device-code client
  asks to become public in the first place.
