import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from authapp.bearer import InvalidBearerToken, decode_bearer_token
from authapp.throttle import AUTHORIZATION_LIMIT_PER_MINUTE, is_throttled, throttled_response
from fakts import base_models, models
from fakts.services import clients, device_codes, rendering

logger = logging.getLogger(__name__)


def _parse(request, model, *, error_key="error"):
    """Parse the JSON request body into ``model``.

    Returns ``(instance, None)`` on success or ``(None, JsonResponse)`` with the
    standard malformed-request envelope on failure.
    """
    try:
        return model(**json.loads(request.body)), None
    except Exception as e:
        logger.error(e, exc_info=True)
        return None, JsonResponse({"status": "error", error_key: f"Malformed request: {str(e)}"})


def _status(status, message):
    return JsonResponse({"status": status, "message": message})


def _absolute_configure_url(template: str, base_url: str) -> str:
    """Resolve the configured `configure_url` to an **absolute** URL for the client.

    The well-known must always hand the client an absolute URL, so we resolve the
    three shapes a deployment may configure:

    - a value with a scheme (``https://host/configure/{code}``) is used verbatim;
    - a root-relative path (``/configure/{code}``) is joined to ``base_url`` (the
      deployment's base domain);
    - a bare host (``go.arkitekt.live/configure/{code}``) is promoted to ``https``.

    The literal ``{code}`` placeholder is preserved — the client substitutes it with
    the device code, so we only ever concatenate, never ``.format()`` it here.
    """
    if "://" in template:
        return template
    if template.startswith("/"):
        return base_url.rstrip("/") + template
    return "https://" + template


@method_decorator(csrf_exempt, name="dispatch")
class WellKnownFakts(View):
    """Well Known fakts Viewset (only allows get). Sends back the well known
    configuration for the fakts server, describing the endpoints for "Claim",
    "Configure", the device-code "start" and "challenge" flows, as well as the
    name and version of the Fakts Protocol."""

    def get(self, request, format=None):
        from authapp.server import GRANT_TYPES_SUPPORTED, TOKEN_ENDPOINT_AUTH_METHODS_SUPPORTED

        # The deployment's base domain — also the base a root-relative configure_url
        # resolves against. (frontend_url is kept for back-compat but is deprecated in
        # favour of the explicit, always-absolute `configure` endpoint below.)
        base_domain = request.build_absolute_uri(reverse("mainhome")).replace(f"/{settings.MY_SCRIPT_NAME}", "")
        return JsonResponse(
            data=base_models.WellKnownFakts(
                name=settings.DEPLOYMENT_NAME,
                version=settings.FAKTS_PROTOCOL_VERSION,
                description=settings.DEPLOYMENT_DESCRIPTION,
                base_url=request.build_absolute_uri(reverse("fakts:index")),
                frontend_url=base_domain,
                configure=_absolute_configure_url(settings.DEPLOYMENT_CONFIGURE_URL, base_domain),
                issuer=settings.OIDC_ISSUER,
                device_authorization_endpoint=request.build_absolute_uri(reverse("app_authorization")),
                token_endpoint=request.build_absolute_uri(reverse("token")),
                jwks_uri=request.build_absolute_uri(reverse("jwks")),
                grant_types_supported=GRANT_TYPES_SUPPORTED,
                token_endpoint_auth_methods_supported=TOKEN_ENDPOINT_AUTH_METHODS_SUPPORTED,
                mesh_coord_url=settings.IONSCALE_COORD_URL,
                mesh_device_code_start=request.build_absolute_uri(reverse("fakts:meshstart")),
                mesh_challenge_url=request.build_absolute_uri(reverse("fakts:meshchallenge")),
                mesh_configure=_absolute_configure_url(settings.DEPLOYMENT_MESH_CONFIGURE_URL, base_domain),
                hub_authorization_endpoint=request.build_absolute_uri(reverse("hub_authorization")),
                hub_claim=request.build_absolute_uri(reverse("fakts:hubclaim")),
                hub_configure=_absolute_configure_url(settings.DEPLOYMENT_HUB_CONFIGURE_URL, base_domain),
            ).model_dump()
        )


@method_decorator(csrf_exempt, name="dispatch")
class AppAuthorizationView(View):
    """The app authorization endpoint — the canonical grant's front door,
    served at /o/app-authorization/ next to the token endpoint.

    RFC 8628 device authorization doubling as dynamic client registration: the
    manifest in the request mints a public OAuth2 client, and the app then
    polls the OAuth2 token endpoint with
    grant_type=urn:ietf:params:oauth:grant-type:device_code as that client."""

    def post(self, request, *args, **kwargs):
        if is_throttled(request, "authorization", AUTHORIZATION_LIMIT_PER_MINUTE):
            return throttled_response()

        start_grant, err = _parse(request, base_models.DeviceCodeStartRequest)
        if err:
            return err

        try:
            device_code = device_codes.start_device_code(start_grant)
        except device_codes.LogoDownloadError:
            return JsonResponse({"status": "error", "error": "Error downloading logo"})

        # Opportunistically reap expired, never-approved codes so their orphan
        # dynamically-registered OAuth2 clients don't accumulate.
        device_codes.purge_expired_device_codes()

        base_domain = request.build_absolute_uri(reverse("mainhome")).replace(f"/{settings.MY_SCRIPT_NAME}", "")
        configure_template = _absolute_configure_url(settings.DEPLOYMENT_CONFIGURE_URL, base_domain)

        return JsonResponse(
            {
                "status": "granted",
                # `device_code` is the full-entropy polling secret; `user_code`
                # is the short human-transcribable code the configure URL carries.
                "device_code": device_code.secret,
                "user_code": device_code.code,
                "client_id": device_code.client.client_id,
                "token_endpoint": request.build_absolute_uri(reverse("token")),
                "verification_uri": configure_template,
                "verification_uri_complete": configure_template.replace("{code}", device_code.code),
                "expires_in": device_code.get_expires_in(),
                "interval": device_code.interval,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class HubAuthorizationView(View):
    """The hub authorization endpoint — the canonical grant's front door for
    whole-hub provisioning, served at /o/hub-authorization/.

    Same shape as app authorization: the hub manifest dynamically registers a
    public OAuth2 client alongside the staged code; a human accepts in kontrol
    (creating the hub inside an organization); the hub server then polls the
    token endpoint with the device-code grant and receives tokens + its
    rendered hub config in one response."""

    def post(self, request, *args, **kwargs):
        if is_throttled(request, "authorization", AUTHORIZATION_LIMIT_PER_MINUTE):
            return throttled_response()

        start_grant, err = _parse(request, base_models.HubStartRequest)
        if err:
            return err

        try:
            device_code = device_codes.start_hub_device_code(start_grant)
        except device_codes.LogoDownloadError:
            return JsonResponse({"status": "error", "error": "Error downloading logo"})

        device_codes.purge_expired_device_codes()

        base_domain = request.build_absolute_uri(reverse("mainhome")).replace(f"/{settings.MY_SCRIPT_NAME}", "")
        configure_template = _absolute_configure_url(settings.DEPLOYMENT_HUB_CONFIGURE_URL, base_domain)

        return JsonResponse(
            {
                "status": "granted",
                "device_code": device_code.secret,
                "user_code": device_code.code,
                "client_id": device_code.client.client_id,
                "token_endpoint": request.build_absolute_uri(reverse("token")),
                "verification_uri": configure_template,
                "verification_uri_complete": configure_template.replace("{code}", device_code.code),
                "expires_in": device_code.get_expires_in(),
                "interval": device_code.interval,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class MeshStartChallengeView(View):
    """Start endpoint for the mesh device-code flow (a machine joining an org mesh)."""

    def post(self, request, *args, **kwargs):
        start_grant, err = _parse(request, base_models.MeshDeviceCodeStartRequest)
        if err:
            return err

        device_code = device_codes.start_mesh_device_code(start_grant)

        return JsonResponse({"status": "granted", "code": device_code.code, "challenge": device_code.challenge_code})


@method_decorator(csrf_exempt, name="dispatch")
class MeshChallengeView(View):
    """Poll endpoint for the mesh device-code flow.

    The mesh flow stays outside the OAuth token endpoint: the minted result is
    an ``IonscaleAuthKey`` (a tailnet pre-auth key, not an OAuth token) and the
    machine needs the coordination URL and the authorized machine name.
    """

    def post(self, request, *args, **kwargs):
        challenge, err = _parse(request, base_models.DeviceCodeChallengeRequest)
        if err:
            return err

        try:
            device_code = models.MeshDeviceCode.objects.get(challenge_code=challenge.code)
        except models.MeshDeviceCode.DoesNotExist:
            return JsonResponse({"status": "error", "error": "Challenge does not exist"})

        if timezone.now() > device_code.expires_at:
            device_code.delete()
            return _status("expired", "The user has not given an answer in enough time")

        if device_code.denied:
            device_code.delete()
            return _status("denied", "The user has denied the request")

        auth_key = device_code.auth_key
        if auth_key:
            return JsonResponse(
                {
                    "status": "granted",
                    "ionscale_auth_key": auth_key.key,
                    "ionscale_coord_url": settings.IONSCALE_COORD_URL,
                    "machine_name": device_code.machine_name,
                }
            )

        return _status("pending", "User has not verified the challenge")


@method_decorator(csrf_exempt, name="dispatch")
class ClaimHubView(View):
    """Retrieve a hub faktsclaim given a hub token."""

    def post(self, request, *args, **kwargs):
        claim, err = _parse(request, base_models.ServerClaimRequest, error_key="message")
        if err:
            return err

        try:
            hub = models.Hub.objects.get(token=claim.token)
            context = rendering.create_serverlinking_context(request, hub, claim)
            config = rendering.render_server_fakts(hub, context)
            return JsonResponse({"status": "granted", "config": config.model_dump()})
        except models.Hub.DoesNotExist:
            return _status("error", "No Hub found for this token")
        except Exception as e:
            logger.error(e, exc_info=True)
            return _status("error", "Error creating configuration")


@method_decorator(csrf_exempt, name="dispatch")
class ReportView(View):
    """Record a client's self-report (functional flag + alias reports).

    Authenticated with the client's Bearer access token — the JWT's `client_id`
    claim identifies the reporting client."""

    def post(self, request, *args, **kwargs):
        try:
            claims = decode_bearer_token(request)
        except InvalidBearerToken as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=401)

        claim, err = _parse(request, base_models.ReportRequest, error_key="message")
        if err:
            return err

        try:
            client = models.Client.objects.get(client_id=claims.get("client_id"))
            clients.report_client(client, claim)
            return _status("reported", "Report processed successfully")
        except models.Client.DoesNotExist:
            return JsonResponse({"status": "error", "message": "No client found for this token"}, status=401)
        except Exception as e:
            logger.error(e, exc_info=True)
            return _status("error", "Error processing report")
