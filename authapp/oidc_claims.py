"""Per-client OIDC claim shaping (``sub`` and ``email``).

Two aspects of the claims lok issues to an OpenID relying party are
configurable **per client** (see ``OAuth2Client.membership_is_subject`` and
``OAuth2Client.email_template``, provisioned from the ``openid_apps`` config):

- **Subject** — by default the ``sub`` claim is the *user* id, so the same
  human is the same subject across every organization they belong to. A client
  can instead opt into the *membership* id as the subject
  (``membership_is_subject``), so each (user, organization) pair is a distinct
  subject.
- **Email** — by default the ``email`` claim is the user's email (falling back
  to a synthetic ``<pk>@users.noreply`` address). A client can instead supply an
  ``email_template`` such as ``"{username}@corp.example"`` rendered from a fixed
  set of membership variables.

The variable set and template validation here are **pure** (stdlib only, no
Django imports) so the config layer (``lok_server.configuration``) can validate
templates at load time. The render/resolve helpers take a ``Membership`` at
runtime.
"""

import string
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:  # avoid importing Django models at config-load time
    from karakter.models import Membership


#: Variable names an ``email_template`` may reference. Kept flat (no attribute
#: or index access) so validation stays simple and templates can't reach into
#: arbitrary object internals.
EMAIL_TEMPLATE_VARIABLES = frozenset(
    {
        "username",
        "user_id",
        "email",
        "membership_id",
        "org_slug",
        "org_name",
    }
)


def validate_email_template(template: str) -> None:
    """Validate an ``email_template`` string against the available variables.

    Raises ``ValueError`` if the template references an unknown variable, uses
    attribute/index access (e.g. ``{user.email}`` or ``{roles[0]}``), or has no
    substitutable content. The message lists the offending and allowed names so
    a misconfiguration is actionable at boot rather than at first login.
    """
    try:
        parsed = list(string.Formatter().parse(template))
    except ValueError as exc:  # malformed braces, e.g. a stray "{"
        raise ValueError(f"email_template {template!r} is not a valid format string: {exc}") from exc

    field_names = [field for _, field, _, _ in parsed if field is not None]
    if not field_names:
        raise ValueError(
            f"email_template {template!r} contains no variables — it would render the same "
            f"email for every user. Include at least one of: {_allowed()}."
        )

    unknown = [f for f in field_names if f not in EMAIL_TEMPLATE_VARIABLES]
    if unknown:
        raise ValueError(
            f"email_template {template!r} references unknown variable(s) "
            f"{', '.join(repr(u) for u in unknown)}. Available variables: {_allowed()}. "
            f"Attribute/index access (e.g. '{{user.email}}') is not allowed."
        )


def _allowed() -> str:
    return ", ".join(sorted(EMAIL_TEMPLATE_VARIABLES))


def build_email_variables(membership: "Membership") -> Dict[str, str]:
    """Build the substitution dict for ``email_template`` from a membership.

    Nullable source fields (``user.email``, ``organization.slug/name``) coerce to
    the empty string so a template never renders the literal ``"None"``.
    """
    user = membership.user
    organization = membership.organization
    return {
        "username": user.username or "",
        "user_id": str(user.id),
        "email": user.email or "",
        "membership_id": str(membership.id),
        "org_slug": organization.slug or "",
        "org_name": organization.name or "",
    }


def resolve_sub(membership: "Membership", membership_is_subject: bool) -> str:
    """Resolve the ``sub`` claim for a membership given the client's policy.

    Must be computed identically for the id_token and the userinfo response —
    OIDC requires the two ``sub`` values to match (Core §5.3.2).
    """
    if membership_is_subject:
        return str(membership.id)
    return str(membership.user.id)


def resolve_email(membership: "Membership", email_template: Optional[str]) -> str:
    """Resolve the ``email`` claim for a membership given the client's policy.

    When ``email_template`` is set it is rendered from ``build_email_variables``;
    otherwise the default is the user's email, falling back to a synthetic
    ``<membership pk>@users.noreply`` address.
    """
    if email_template:
        return email_template.format_map(build_email_variables(membership))
    return membership.user.email or f"{membership.pk}@users.noreply"
