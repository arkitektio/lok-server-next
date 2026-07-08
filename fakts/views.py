import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

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


def _poll_device_code(device_code, result_attr):
    """Shared polling response for the device-code challenge endpoints."""
    if timezone.now() > device_code.expires_at:
        device_code.delete()
        return _status("expired", "The user has not given an answer in enough time")

    if device_code.denied:
        device_code.delete()
        return _status("denied", "The user has denied the request")

    # the related object is only set once the user has verified the challenge
    result = getattr(device_code, result_attr)
    if result:
        return JsonResponse({"status": "granted", "token": result.token})

    return _status("pending", "User  has not verfied the challenge")


@method_decorator(csrf_exempt, name="dispatch")
class WellKnownFakts(View):
    """Well Known fakts Viewset (only allows get). Sends back the well known
    configuration for the fakts server, describing the endpoints for "Claim",
    "Configure", the device-code "start" and "challenge" flows, as well as the
    name and version of the Fakts Protocol."""

    def get(self, request, format=None):
        # The deployment's base domain — also the base a root-relative configure_url
        # resolves against. (frontend_url is kept for back-compat but is deprecated in
        # favour of the explicit, always-absolute `configure` endpoint below.)
        base_domain = request.build_absolute_uri(reverse("mainhome")).replace(f"/{settings.MY_SCRIPT_NAME}", "")
        return JsonResponse(
            data=base_models.WellKnownFakts(
                name=settings.DEPLOYMENT_NAME,
                version=settings.FAKTS_PROTOCOL_VERSION,
                description=settings.DEPLOYMENT_DESCRIPTION,
                claim=request.build_absolute_uri(reverse("fakts:claim")),
                base_url=request.build_absolute_uri(reverse("fakts:index")),
                frontend_url=base_domain,
                configure=_absolute_configure_url(settings.DEPLOYMENT_CONFIGURE_URL, base_domain),
                device_code_start=request.build_absolute_uri(reverse("fakts:start")),
                challenge_url=request.build_absolute_uri(reverse("fakts:challenge")),
                mesh_coord_url=settings.IONSCALE_COORD_URL,
                mesh_device_code_start=request.build_absolute_uri(reverse("fakts:meshstart")),
                mesh_challenge_url=request.build_absolute_uri(reverse("fakts:meshchallenge")),
                mesh_configure=_absolute_configure_url(settings.DEPLOYMENT_MESH_CONFIGURE_URL, base_domain),
                hub_device_code_start=request.build_absolute_uri(reverse("fakts:hubstart")),
                hub_challenge_url=request.build_absolute_uri(reverse("fakts:hubchallenge")),
                hub_claim=request.build_absolute_uri(reverse("fakts:hubclaim")),
                hub_configure=_absolute_configure_url(settings.DEPLOYMENT_HUB_CONFIGURE_URL, base_domain),
            ).model_dump()
        )


@method_decorator(csrf_exempt, name="dispatch")
class StartChallengeView(View):
    """An endpoint that is challenged in the course of a device code flow."""

    def post(self, request, *args, **kwargs):
        start_grant, err = _parse(request, base_models.DeviceCodeStartRequest)
        if err:
            return err

        try:
            device_code = device_codes.start_device_code(start_grant)
        except device_codes.LogoDownloadError:
            return JsonResponse({"status": "error", "error": "Error downloading logo"})

        return JsonResponse({"status": "granted", "code": device_code.code})


@method_decorator(csrf_exempt, name="dispatch")
class ServiceStartChallengeView(View):
    """An endpoint that is challenged in the course of a device code flow."""

    def post(self, request, *args, **kwargs):
        start_grant, err = _parse(request, base_models.ServiceDeviceCodeStartRequest)
        if err:
            return err

        try:
            device_code = device_codes.start_service_device_code(start_grant)
        except device_codes.LogoDownloadError:
            return JsonResponse({"status": "error", "error": "Error downloading logo"})

        return JsonResponse({"status": "granted", "code": device_code.code, "challenge": device_code.challenge_code})


@method_decorator(csrf_exempt, name="dispatch")
class HubStartChallengeView(View):
    """An endpoint that is challenged in the course of a device code flow."""

    def post(self, request, *args, **kwargs):
        start_grant, err = _parse(request, base_models.HubStartRequest)
        if err:
            return err

        try:
            device_code = device_codes.start_hub_device_code(start_grant)
        except device_codes.LogoDownloadError:
            return JsonResponse({"status": "error", "error": "Error downloading logo"})

        return JsonResponse({"status": "granted", "code": device_code.code, "challenge": device_code.challenge_code})


@method_decorator(csrf_exempt, name="dispatch")
class HubChallengeView(View):
    """An endpoint that is challenged in the course of a device code flow."""

    def post(self, request, *args, **kwargs):
        challenge, err = _parse(request, base_models.DeviceCodeChallengeRequest)
        if err:
            return err

        try:
            device_code = models.HubDeviceCode.objects.get(challenge_code=challenge.code)
        except models.HubDeviceCode.DoesNotExist:
            return JsonResponse({"status": "error", "error": "Challenge does not exist"})

        return _poll_device_code(device_code, "hub")


@method_decorator(csrf_exempt, name="dispatch")
class ServiceChallengeView(View):
    """An endpoint that is challenged in the course of a device code flow."""

    def post(self, request, *args, **kwargs):
        challenge, err = _parse(request, base_models.DeviceCodeChallengeRequest)
        if err:
            return err

        try:
            device_code = models.ServiceDeviceCode.objects.get(challenge_code=challenge.code)
        except models.ServiceDeviceCode.DoesNotExist:
            return JsonResponse({"status": "error", "error": "Challenge does not exist"})

        return _poll_device_code(device_code, "instance")


@method_decorator(csrf_exempt, name="dispatch")
class ChallengeView(View):
    """An endpoint that is challenged in the course of a device code flow."""

    def post(self, request, *args, **kwargs):
        challenge, err = _parse(request, base_models.DeviceCodeChallengeRequest)
        if err:
            return err

        try:
            device_code = models.DeviceCode.objects.get(code=challenge.code)
        except models.DeviceCode.DoesNotExist:
            return JsonResponse({"status": "error", "error": "Challenge does not exist"})

        return _poll_device_code(device_code, "client")


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

    Unlike the client/service/hub challenge views this does not reuse
    ``_poll_device_code``: the minted result is an ``IonscaleAuthKey`` (which exposes
    ``.key``, not ``.token``) and the machine needs the coordination URL and the
    authorized machine name in addition to the key.
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
class RetrieveView(View):
    """
    Implements an endpoint that returns the faktsclaim for a given identifier and version
    if the app was already configured and the app is marked as PUBLIC. While any app can
    request a faktsclaim for any other app, redirect uris are set to predifined values
    and the app will not be able to use the faktsclaim to get a configuration.
    """

    def post(self, request, *args, **kwargs):
        retrieve, err = _parse(request, base_models.RetrieveRequest)
        if err:
            return err

        try:
            app = models.App.objects.get(identifier=retrieve.manifest.identifier)
            release = models.Release.objects.get(app=app, version=retrieve.manifest.version)
        except models.Release.DoesNotExist:
            return _status("error", f"Release does not exist {retrieve.manifest.identifier}:{retrieve.manifest.version}")
        except models.App.DoesNotExist:
            return _status("error", f"App does not exist {retrieve.manifest.identifier}")

        client = release.clients.filter(public=True).first()
        if not client:
            return _status("error", "There is no client for this app that is public. Please use a different grant")

        return JsonResponse({"status": "granted", "token": client.token})


@method_decorator(csrf_exempt, name="dispatch")
class RedeemView(View):
    """
    Implements an endpoint that redeems a pre-issued token into a client token.
    """

    def post(self, request, *args, **kwargs):
        redeem_request, err = _parse(request, base_models.ReedeemTokenRequest)
        if err:
            return err

        try:
            client = clients.redeem_token(
                redeem_request.token,
                redeem_request.manifest,
                role=redeem_request.requested_client_role,
            )
        except models.RedeemToken.DoesNotExist:
            return _status("error", "Invalid redeem token")
        except clients.RedeemTokenExpired:
            return _status("error", "Redeem token expired")
        except clients.RedeemTokenManifestChanged as e:
            return _status("error", str(e))
        except Exception as e:
            logger.error(e, exc_info=True)
            return _status("error", str(e))

        return JsonResponse({"status": "granted", "token": client.token})


@method_decorator(csrf_exempt, name="dispatch")
class ClaimView(View):
    """Retrieve a faktsclaim given a client token generated by the platform."""

    def post(self, request, *args, **kwargs):
        claim, err = _parse(request, base_models.ClaimRequest, error_key="message")
        if err:
            return err

        try:
            client = models.Client.objects.get(token=claim.token)
            context = rendering.create_linking_context(request, client, claim)
            config = rendering.render_hub(client, context)
            return JsonResponse({"status": "granted", "config": config})
        except models.Client.DoesNotExist:
            return _status("error", "No Client found for this token")
        except Exception as e:
            logger.error(e, exc_info=True)
            return _status("error", "Error creating configuration")


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
    """Record a client's self-report (functional flag + alias reports)."""

    def post(self, request, *args, **kwargs):
        claim, err = _parse(request, base_models.ReportRequest, error_key="message")
        if err:
            return err

        try:
            clients.report_client(claim)
            return _status("reported", "Report processed successfully")
        except models.Client.DoesNotExist:
            return _status("error", "No Client found for this token")
        except Exception as e:
            logger.error(e, exc_info=True)
            return _status("error", "Error creating configuration")
