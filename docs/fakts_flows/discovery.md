# Discovery (`/.well-known/fakts`)

> Shared step — the **entry point** every flow starts from, not a flow on its own.

A client knows only the deployment's base URL. It `GET`s `/.well-known/fakts` to
learn the absolute URLs of every fakts endpoint and a few deployment facts, then
drives whichever [flow](./README.md#2-which-flow-when) it needs. This keeps endpoint
paths and the mesh coordinator out of client configuration — the server is the
single source of truth.

- [When to use](#when-to-use)
- [Why](#why)
- [Request](#request)
- [Response fields](#response-fields)
- [Code path](#code-path)

## When to use

Always, first — before start/retrieve/redeem. A client should treat the URLs it
returns as authoritative rather than hard-coding `/f/...` paths, so a deployment can
relocate endpoints or sit behind a gateway without breaking clients.

## Why

Fakts is designed so a client ships with *only* a base URL. Discovery is what turns
that one URL into a working set of endpoints, and it is where per-deployment facts
(the human `configure` page template, the mesh coordinator URL) are advertised.
Because the server builds these as absolute URLs from the incoming request, the same
image works across dev/staging/prod without reconfiguration.

## Request

`GET /.well-known/fakts` — no body, no auth. Returns a JSON object
(`WellKnownFakts`). There are no sendable params.

## Response fields

| Field | Type | Description |
|---|---|---|
| `name` | str | Deployment name. |
| `version` | str | Fakts protocol version of this deployment. |
| `protocol_version` | str | Protocol version marker (`"1"`). |
| `description` | str? | Deployment description. |
| `claim` | str | Absolute URL of the [claim](./claim.md) endpoint. |
| `base_url` | str | Absolute base of the fakts endpoints (`/f/`). |
| `frontend_url` | str | Deployment base domain. *Deprecated* — prefer `configure`. |
| `configure` | str? | Absolute [client-configure](./client_device_code.md) page template; the literal `{code}` is substituted by the client. |
| `device_code_start` | str? | Absolute URL of the client [start](./client_device_code.md) endpoint. |
| `challenge_url` | str? | Absolute URL of the client [challenge](./client_device_code.md) endpoint. |
| `mesh_coord_url` | str? | Public ionscale [mesh](./mesh_device_code.md) coordination URL, or `null` when no mesh is configured. |
| `mesh_device_code_start` | str? | Absolute URL of the [mesh start](./mesh_device_code.md) endpoint. |
| `mesh_challenge_url` | str? | Absolute URL of the [mesh challenge](./mesh_device_code.md) endpoint. |
| `mesh_configure` | str? | Absolute [mesh-configure](./mesh_device_code.md) page template; `{code}` is substituted by the machine. |
| `hub_device_code_start` | str? | Absolute URL of the [hub start](./hub_device_code.md) endpoint. |
| `hub_challenge_url` | str? | Absolute URL of the [hub challenge](./hub_device_code.md) endpoint. |
| `hub_claim` | str? | Absolute URL of the [hub claim](./claim.md#hub-claim) endpoint. |
| `hub_configure` | str? | Absolute [hub-configure](./hub_device_code.md) page template; `{code}` is substituted by the client. |

> The document advertises the *client*, *mesh*, and *hub* device-code
> endpoints explicitly. The *service* endpoints (`/f/servicestart/`,
> `/f/servicechallenge/`) are not yet advertised here — they follow the fixed
> `/f/service*` naming under `base_url`.

## Code path

- View: `WellKnownFakts` (`fakts/views.py`), mounted at `.well-known/fakts`
  (`lok_server/urls.py`).
- Model: `WellKnownFakts` (`fakts/base_models.py`).
- `configure` / `mesh_configure` are resolved to absolute URLs by
  `_absolute_configure_url` from `DEPLOYMENT_CONFIGURE_URL` /
  `DEPLOYMENT_MESH_CONFIGURE_URL` (see [CONFIG.md](../../CONFIG.md), `configure_url`
  / `mesh_configure_url`).
