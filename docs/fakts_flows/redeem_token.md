# Redeem token

A **non-interactive** flow: an operator pre-issues a one-time `RedeemToken` (bound to
a hub and an expiry), then a headless machine exchanges that token — plus its
manifest — for a fully provisioned client, with **no human in the loop at redeem
time**. The authorization happened once, up front, when the token was minted.

- [When to use](#when-to-use)
- [Why](#why)
- [Protocol](#protocol)
- [Sendable params](#sendable-params)
- [Manifest change rules](#manifest-change-rules)
- [Responses](#responses)
- [Code path](#code-path)

## When to use

- You are provisioning a client **without an interactive browser step** — CI, image
  bake, autoscaled workers, kiosk installs.
- You can distribute a secret token to the machine ahead of time (env var, secret
  mount).
- You want repeatable installs: the same token + same manifest yields the same
  client.

Use a [device-code flow](./client_device_code.md) when a human *is* present to
approve; use [retrieve](./retrieve.md) when the app is public and needs no token.

## Why

Device-code needs a human at configure time, which is exactly what headless
automation lacks. The redeem token moves the human decision **earlier**: a user
creates the token once (choosing the hub and lifetime), and every machine
that holds it can non-interactively obtain a client. Redeem is idempotent for an
unchanged manifest, so re-running an installer returns the existing client's token
instead of proliferating clients.

## Protocol

1. **Mint** (out of band, by a human) — create a `RedeemToken` via the management
   GraphQL. `createRedeemToken(input: {hub, expiresInDays})` takes the
   hub (the caller must be a member of its org) and an optional lifetime in
   days. (`allow_reredeem` is a field on the token model but is **not** exposed by
   this mutation today — it defaults to `false`.)
2. **Redeem** — the machine `POST /f/redeem/` with `{token, manifest}` ⇒
   `{status: granted, token}` (the client token). Claim it as usual (see
   [claim](./claim.md)).

## Endpoints

| Step | Method | Path | URL name |
|---|---|---|---|
| Redeem | POST | `/f/redeem/` | `fakts:redeem` |

## Sendable params

### `ReedeemTokenRequest`
`POST /f/redeem/`

| Field | Type | Default | Description |
|---|---|---|---|
| `token` | str | — (required) | The pre-issued redeem token. |
| `manifest` | [`Manifest`](./README.md#manifest) | — (required) | The client to provision. |
| `requested_client_role` | enum | `"interface"` | Operational role: `interface` \| `agent`. |
| `supported_layers` | str[] | `["web"]` | Requested network layers. **Note:** accepted but not currently consumed by the redeem path. |

## Manifest change rules

A redeem token remembers the hash of the manifest it was first redeemed with:

- **Same manifest** → returns the **same** client token (idempotent re-install).
- **Changed manifest** → rejected with an error mentioning `allow_reredeem`, unless
  the token has `allow_reredeem=true` set on it.
- **Legacy tokens** (redeemed before hash tracking) have a null hash and are
  grandfathered: a changed manifest is accepted once and the hash backfilled.

## Responses

| Endpoint | Success | Non-success |
|---|---|---|
| `/f/redeem/` | `{status: granted, token}` | `{status: error, message}` — e.g. `"Invalid redeem token"`, expired, or manifest-changed-without-`allow_reredeem`. |

## Code path

- REST: `RedeemView` (`fakts/views.py`).
- Service: `redeem_token`, `validate_redeem_token` (`fakts/services/clients.py`);
  errors `RedeemTokenExpired`, `RedeemTokenManifestChanged`.
- Model: `RedeemToken` (`fakts/models.py`), fields `token`, `hub`,
  `manifest_hash`, `allow_reredeem`, `expires_at`, `client`.
- GraphQL (minting): `create_redeem_token`
  (`api/management/mutations/redeem_token.py`), `ManagementRedeemToken` type.
- Frontend (minting): `src/components/CreateRedeemTokenDialog.tsx`.
