# Social accounts

How lok lets users sign in with an external identity provider — Google, GitHub,
ORCID, and any other [django-allauth](https://docs.allauth.org/) social provider
— and how those external identities are linked to lok users.

- [1. Overview: how social accounts work](#1-overview-how-social-accounts-work)
- [2. The login flow end to end](#2-the-login-flow-end-to-end)
- [3. How it appears at login (the SPA)](#3-how-it-appears-at-login-the-spa)
- [4. Configuration](#4-configuration)
- [5. Support: providers, adding new ones, limitations](#5-support-providers-adding-new-ones-limitations)

---

## 1. Overview: how social accounts work

Lok delegates social login to the bundled `allauth.socialaccount` Django app.
The moving parts:

| Concept | What it is |
|---|---|
| **Provider** | An external identity service (e.g. `google`). Enabled by installing its allauth app. |
| **`SocialApp`** | The OAuth **credentials** for one provider — the `client_id` / `secret` you register with that provider. In lok these come from config (`socialaccount_providers`), not the database. |
| **`SocialAccount`** | The **link** between a lok `User` and their identity at a provider (the provider's user id + profile data). One user can have several. |
| **`SocialToken`** | The OAuth access/refresh token allauth stores for a linked account. |
| **`EmailAddress`** | allauth's email records. Social login uses these to **match or verify** users by email (see [§4](#4-configuration)). |

A social login is an **OAuth 2.0 / OpenID Connect authorization-code flow**: lok
never sees the user's password at the provider; it receives a short-lived code,
exchanges it (using the `SocialApp` secret) for tokens, reads the user's profile,
and then either logs in an existing linked user or creates/links one.

This composes with the two "worlds" described in
[`../../CONFIG.md`](../../CONFIG.md#username-world-vs-email-world): social login
works regardless of whether local login uses `username` or `email`.

## 2. The login flow end to end

1. **Button** — the SPA shows a "Login with Google" button for each enabled
   provider (it learns the list from the allauth capability config, see [§3](#3-how-it-appears-at-login-the-spa)).
2. **Redirect** — clicking it POSTs to the headless endpoint
   `…/auth/provider/redirect` with the provider id and a `callback_url`; allauth
   redirects the browser to the provider's consent screen.
3. **Consent** — the user authenticates at the provider and approves the
   requested `SCOPE`s.
4. **Callback** — the provider redirects back to lok at
   **`https://<host>/lok/accounts/<provider>/login/callback/`**. allauth
   validates the `state`, exchanges the code for tokens using the `SocialApp`
   secret, and fetches the user's profile.
5. **Link or create** — allauth resolves the identity:
   - Known `SocialAccount` → log that user in.
   - New identity whose email matches an existing verified `EmailAddress` and
     `EMAIL_AUTHENTICATION`/`VERIFIED_EMAIL` allow it → link to that user.
   - Otherwise → create a new user + `SocialAccount` (a signup).
6. **Back to the SPA** — allauth returns the browser to the `callback_url` the
   SPA supplied; the SPA finalizes the session.

> The callback URL in step 4 is the one you must register in the **provider's**
> developer console. Verify it for your deployment — its host depends on where
> lok is served and its prefix on `django.force_script_name` (default `lok`).

## 3. How it appears at login (the SPA)

The kontrol SPA renders social login purely from what the server advertises — no
provider is hard-coded in the frontend:

- The headless config endpoint returns `socialaccount.providers` (id, name,
  flows) for every enabled provider.
- `kontrol/src/socialaccount/ProviderList.tsx` reads that list and renders a
  button per provider; the Login and Signup pages include it when the list is
  non-empty.
- The button calls `redirectToProvider()` in `kontrol/src/lib/allauth.ts`, which
  kicks off step 2 above; the return trip is handled by
  `kontrol/src/Callback.tsx` / `ProviderCallback.tsx`.
- Linked accounts are managed after login in
  `kontrol/src/socialaccount/ManageProviders.tsx`.

Practical consequence: **enable/configure a provider on the server and its button
appears automatically** — there is no matching frontend change to make.

## 4. Configuration

Enabling a provider is **two coupled steps**, both in the lok config
(`config.yaml` / env). The exhaustive field reference lives in
[`../../CONFIG.md` → Social login providers](../../CONFIG.md#social-login-providers);
this is the summary.

1. **Install the provider app** — add its dotted path to
   `account.social_provider_apps` (appended to `INSTALLED_APPS`).
2. **Configure its OAuth app** — add a **typed** entry under
   `socialaccount_providers`, keyed by provider id, with the `client_id` /
   `secret` from that provider.

```yaml
account:
  social_provider_apps:
    - allauth.socialaccount.providers.google

socialaccount_providers:
  google:
    APP:
      client_id: "1234567890-abc.apps.googleusercontent.com"
      secret: "GOCSPX-your-secret"   # 🔒 inject per deployment; never commit
    SCOPE: [profile, email]
    OAUTH_PKCE_ENABLED: true
```

The `socialaccount_providers` block is validated by pydantic
(`lok_server/configuration.py`: `SocialProviderConfig` / `SocialAppConfig`): a
missing or mistyped credential key is rejected **at boot** with the exact path,
while provider-specific extras (e.g. `FETCH_USERINFO`) still pass through. It is
converted to allauth's `SOCIALACCOUNT_PROVIDERS` in `lok_server/settings.py`.

### Email linking and the account world

Two per-provider flags govern how a social identity connects to a lok user:

- **`VERIFIED_EMAIL: true`** — trust the email the provider returns as already
  verified. Under **mandatory** email verification this lets social signups skip
  the confirmation email (the provider has already verified it).
- **`EMAIL_AUTHENTICATION: true`** — if the provider's email matches an existing
  account, log into / link that account instead of creating a duplicate.

Set these deliberately: enabling them for a provider that does **not** actually
verify emails would let someone take over an account by email. Only trust
`VERIFIED_EMAIL` for providers that guarantee verified emails (e.g. Google).

## 5. Support: providers, adding new ones, limitations

**Enabled by default.** The shipped `account.social_provider_apps` default is
`orcid` and `google`. They still need credentials in `socialaccount_providers`
to actually work — no credentials means the button won't render.

**Adding any provider.** allauth ships dozens
([provider index](https://docs.allauth.org/en/latest/socialaccount/providers/index.html)).
For each: install its app (step 1), add its credentials (step 2), and register
the callback URL from [§2](#2-the-login-flow-end-to-end) in the provider's
console. Provider-specific settings (scopes, extra params) go in the same typed
entry — common keys are documented in CONFIG.md, and unknown keys are accepted
verbatim.

**Secrets.** Every `secret` is sensitive. Inject it via environment
(`SOCIALACCOUNT_PROVIDERS__…`) or a secret file per deployment; never commit real
credentials.

**Limitations / notes.**
- Credentials are configured **via settings**, not the Django admin
  `SocialApp` table. Rows added in the admin are additive but are not what these
  docs describe.
- Some providers (SAML, generic OpenID Connect) use sub-providers — set
  `provider_id` / use `APPS` for multiple instances.

> **⚠️ 2026 disclaimer.** OAuth provider consoles, endpoint URLs, required
> scopes, callback-URL formats, and app-review/verification policies change
> frequently and differ per provider. Everything here was accurate as of
> **2026** and is illustrative — always follow the **provider's current developer
> documentation** and
> [allauth's per-provider docs](https://docs.allauth.org/en/latest/socialaccount/providers/index.html)
> for the exact credential fields, scopes, and callback URL for your deployment.
