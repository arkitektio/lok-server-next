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
    """Well Known fakts Viewset (only allows get). Sends
    back the well known configuration for the fakts server Describing
    endpoints for "Claim" and "Configure" as well as the name and version.
    Of the Fakts Protocol"""

    def get(self, request, format=None):
        try:
            with open(settings.CA_FILE, "r") as f:
                ca = f.read()
        except Exception:
            ca = None

        return JsonResponse(
            data=base_models.WellKnownFakts(
                name=settings.DEPLOYMENT_NAME,
                version=settings.FAKTS_PROTOCOL_VERSION,
                description=settings.DEPLOYMENT_DESCRIPTION,
                claim=request.build_absolute_uri(reverse("fakts:claim")),
                base_url=request.build_absolute_uri(reverse("fakts:index")),
                frontend_url=request.build_absolute_uri(reverse("mainhome")).replace(f"/{settings.MY_SCRIPT_NAME}", ""),
                ca_crt=ca,
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
class CompositionStartChallengeView(View):
    """An endpoint that is challenged in the course of a device code flow."""

    def post(self, request, *args, **kwargs):
        start_grant, err = _parse(request, base_models.CompositionStartRequest)
        if err:
            return err

        try:
            device_code = device_codes.start_composition_device_code(start_grant)
        except device_codes.LogoDownloadError:
            return JsonResponse({"status": "error", "error": "Error downloading logo"})

        return JsonResponse({"status": "granted", "code": device_code.code, "challenge": device_code.challenge_code})


@method_decorator(csrf_exempt, name="dispatch")
class CompositionChallengeView(View):
    """An endpoint that is challenged in the course of a device code flow."""

    def post(self, request, *args, **kwargs):
        challenge, err = _parse(request, base_models.DeviceCodeChallengeRequest)
        if err:
            return err

        try:
            device_code = models.CompositionDeviceCode.objects.get(challenge_code=challenge.code)
        except models.CompositionDeviceCode.DoesNotExist:
            return JsonResponse({"status": "error", "error": "Challenge does not exist"})

        return _poll_device_code(device_code, "composition")


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
            config = rendering.render_composition(client, context)
            return JsonResponse({"status": "granted", "config": config})
        except models.Client.DoesNotExist:
            return _status("error", "No Client found for this token")
        except Exception as e:
            logger.error(e, exc_info=True)
            return _status("error", "Error creating configuration")


@method_decorator(csrf_exempt, name="dispatch")
class ClaimCompositionView(View):
    """Retrieve a composition faktsclaim given a composition token."""

    def post(self, request, *args, **kwargs):
        claim, err = _parse(request, base_models.ServerClaimRequest, error_key="message")
        if err:
            return err

        try:
            composition = models.Composition.objects.get(token=claim.token)
            context = rendering.create_serverlinking_context(request, composition, claim)
            config = rendering.render_server_fakts(composition, context)
            return JsonResponse({"status": "granted", "config": config.model_dump()})
        except models.Client.DoesNotExist:
            return _status("error", "No Client found for this token")
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
