from kante import Info
import strawberry
from authapp.models import AuthorizationCode, OAuth2Client
import kante
from urllib.parse import urlencode
import secrets
from django.utils import timezone
from karakter import models


@kante.input
class AcceptAuthorizeCodeInput:
    """Input for accepting an authorize code request"""

    organization: str
    client_id: str
    redirect_uri: str
    scope: str
    state: str
    nonce: str | None = None


def accept_authorize_code(info: Info, input: AcceptAuthorizeCodeInput) -> str:
    """
    Accept an authorize code request.

    Create an authorization code for the user and client, and return the redirect URI.
    """
    user = info.context.request.user
    if not user.is_authenticated:
        raise Exception("User not authenticated")

    try:
        client = OAuth2Client.objects.get(client_id=input.client_id)
    except OAuth2Client.DoesNotExist:
        raise Exception("Client not found")

    if not client.check_redirect_uri(input.redirect_uri):
        raise Exception("Invalid redirect URI")

    code = secrets.token_urlsafe(48)

    organization = models.Organization.objects.get(id=input.organization)

    membership = models.Membership.objects.filter(user=user, organization=organization).first()
    if not membership:
        raise Exception("User is not a member of the organization")

    auth_code = AuthorizationCode.objects.create(
        membership=membership,
        client_id=input.client_id,
        code=code,
        redirect_uri=input.redirect_uri,
        scope=input.scope,
        nonce=input.nonce,
        auth_time=int(timezone.now().timestamp()),
    )

    params = {
        "code": code,
        "state": input.state,
    }

    return f"{input.redirect_uri}?{urlencode(params)}"


@kante.input
class DeclineAuthorizeCodeInput:
    """Input for declining an authorize code request"""

    client_id: str
    redirect_uri: str
    state: str


def decline_authorize_code(info: Info, input: DeclineAuthorizeCodeInput) -> str:
    """
    Decline an authorize code request.

    Return the redirect URI with an error parameter.
    """
    try:
        client = OAuth2Client.objects.get(client_id=input.client_id)
    except OAuth2Client.DoesNotExist:
        raise Exception("Client not found")

    if not client.check_redirect_uri(input.redirect_uri):
        raise Exception("Invalid redirect URI")

    params = {
        "error": "access_denied",
        "error_description": "The user denied the request",
        "state": input.state,
    }
    return f"{input.redirect_uri}?{urlencode(params)}"
