# Claim

> Shared step — the **tail** of the client and hub flows, not a flow on its
> own.

Once a flow has produced a **token** (a `Client` token from the client / redeem /
retrieve flows, or a `Hub` token from the hub flow), the holder
`POST`s it to a claim endpoint to receive the **rendered configuration** — auth
credentials, service endpoints, and per-requirement grant outcomes — computed for
the requesting host.

- [When to use](#when-to-use)
- [Why](#why)
- [Client claim](#client-claim)
- [Hub claim](#hub-claim)
- [Responses](#responses)
- [Code path](#code-path)

## When to use

After you hold a token and need the actual configuration to run. A client typically
claims on every startup, so the config reflects current instances/aliases rather
than a snapshot frozen at registration time.

## Why

Registration produces a durable identity (a token); the *configuration* is dynamic —
which service instances satisfy the client's requirements, what URLs they currently
advertise, which optional requirements were granted. Separating claim from
registration lets a client re-resolve its world each run without re-authorizing, and
lets the server render host-specific endpoints (the `secure`/host context flows into
alias URL rendering).

## Client claim

`POST /f/claim/` — for a `Client` token.

### `ClaimRequest`
| Field | Type | Default | Description |
|---|---|---|---|
| `token` | str | — (required) | The client token from start→challenge, redeem, or retrieve. |
| `secure` | bool | `false` | Whether the requesting context is secure; affects rendered alias URLs. |

Returns `{status: granted, config}` where `config` is a rendered `ClaimAnswer`:
`self` (deployment + self alias), `auth` (`client_id`, `client_secret`,
`client_token`, `token_url`, `report_url`, `scopes`, optional `ionscale_auth_key`),
`instances` (per requirement, with aliases), and `statuses` (per-requirement
`granted` / `denied` / `unavailable`).

## Hub claim

`POST /f/claimhub/` — for a `Hub` token.

### `ServerClaimRequest`
| Field | Type | Default | Description |
|---|---|---|---|
| `token` | str | — (required) | The hub token from the hub challenge. |

Returns `{status: granted, config}` where `config` is a rendered
`HubClaimAnswer`: `self`, `auth` (`jwks_url`, and — when the hub has
a mesh key — `ionscale_auth_key` + `ionscale_coord_url`), `instances` (with private
keys), and `clients` (with tokens).

## Responses

| Endpoint | Success | Non-success |
|---|---|---|
| `/f/claim/` | `{status: granted, config}` | `{status: error, message}` — e.g. `"No Client found for this token"`. |
| `/f/claimhub/` | `{status: granted, config}` | `{status: error, message}` — e.g. `"No Hub found for this token"`. |

## Code path

- REST: `ClaimView` / `ClaimHubView` (`fakts/views.py`).
- Rendering: `create_linking_context` + `render_hub` (client),
  `create_serverlinking_context` + `render_server_fakts` (hub), all in
  `fakts/services/rendering.py`.
- Models: `ClaimRequest`, `ServerClaimRequest`, `ClaimAnswer`,
  `HubClaimAnswer` (`fakts/base_models.py`).
