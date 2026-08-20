# Redeem token — the headless fakts grant

Provisions a client **non-interactively** from a pre-shared one-time token
(CI, headless installs). Same combined response as the
[canonical device-code grant](./client_device_code.md) — access token, refresh
token and rendered instances in one exchange — but with no human step at
grant time: the authorization happened when a member minted the redeem token.

## 1. Minting a redeem token (human, kontrol)

`createRedeemToken` (management GraphQL) takes a `hub` and an optional
`expiresInDays`. The hub is required and **carries the organization** — the
minting user must be a member, and every client redeemed from the token lands
in that hub's organization, bound to the minting user's membership there.

## 2. Redeeming: `POST /o/token/`

Standard OAuth2 form encoding, custom grant type:

```
grant_type=urn:fakts:grant-type:redeem
redeem_token=…
manifest={"identifier": "com.example.app", "version": "1.0.0", "scopes": [], "requirements": []}
requested_client_role=agent        (optional, default interface)
```

`manifest` is the JSON-serialized [`Manifest`](./README.md#manifest). There is
no client authentication — the redeem token *is* the credential; the fakts
client and its public OAuth2 client are provisioned (or reused) during the
exchange.

On success the response is the same combined token response as the device-code
grant (`access_token`, `refresh_token`, `expires_in`, `scope`, plus
`client_id`, `self`, `instances`, `statuses`). Failures are standard OAuth
errors: HTTP 400 with `error=invalid_grant` (unknown/expired token, or a
changed manifest without `allow_reredeem` — see below) or
`error=invalid_request` (missing/malformed fields).

## 3. Re-redeem semantics

- Redeeming again with the **same manifest** returns the same client (a fresh
  token pair each time).
- A **changed manifest** is rejected unless the token was created with
  `allow_reredeem` — then the client is re-validated against the new manifest.
- An **expired** token is deleted on first use after expiry.

## 4. After the grant

Identical to the device-code grant: refresh with
`grant_type=refresh_token` + `refresh_token` + `client_id` (rotating, 30-day
window, envelope re-rendered on every refresh), authenticate everywhere with
the Bearer JWT.
