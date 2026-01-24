from xmlrpc import client
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
import logging
import json
import datetime
from .utils import (
    download_logo,
)
from django.urls import reverse
from fakts import base_models, enums, models, builders, logic
from django.conf import settings


logger = logging.getLogger(__name__)


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
        except Exception as e:
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
            ).dict()
        )


@method_decorator(csrf_exempt, name="dispatch")
class StartChallengeView(View):
    """
    An endpoint that is challenged in the course of a device code flow.
    """

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)
        try:
            start_grant = base_models.DeviceCodeStartRequest(**json_data)
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": f"Malformed request: {str(e)}",
                }
            )

        manifest = start_grant.manifest

        try:
            logo = download_logo(manifest.logo) if manifest.logo else None
        except Exception as e:
            logger.error(f"Error downloading logo: {manifest.logo}", exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": "Error downloading logo",
                }
            )

        logger.info(f"Received start challenge for {manifest.identifier}:{manifest.version} {start_grant.request_public}")

        device_code = models.DeviceCode.objects.create(
            code=logic.create_device_code(),
            staging_manifest=manifest.dict(),
            expires_at=datetime.datetime.now() + datetime.timedelta(seconds=start_grant.expiration_time_seconds),
            staging_kind=start_grant.requested_client_kind.value,
            staging_redirect_uris=start_grant.redirect_uris,
            staging_logo=logo,
            staging_public=start_grant.request_public,
        )

        return JsonResponse(
            data={
                "status": "granted",
                "code": device_code.code,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class ServiceStartChallengeView(View):
    """
    An endpoint that is challenged in the course of a device code flow.
    """

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)
        try:
            start_grant = base_models.ServiceDeviceCodeStartRequest(**json_data)
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": f"Malformed request: {str(e)}",
                }
            )

        manifest = start_grant.manifest

        try:
            logo = download_logo(manifest.logo) if manifest.logo else None
        except Exception as e:
            logger.error(f"Error downloading logo: {manifest.logo}", exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": "Error downloading logo",
                }
            )

        logger.info(f"Received start challenge for {manifest.identifier}:{manifest.version}")

        device_code = models.ServiceDeviceCode.objects.create(
            code=logic.create_device_code(),
            challenge_code=logic.create_device_code(),
            staging_manifest=manifest.model_dump(),
            staging_aliases=[alias.model_dump() for alias in start_grant.staging_aliases],
            expires_at=datetime.datetime.now() + datetime.timedelta(seconds=start_grant.expiration_time_seconds),
        )

        return JsonResponse(
            data={
                "status": "granted",
                "code": device_code.code,
                "challenge": device_code.challenge_code,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class CompositionStartChallengeView(View):
    """
    An endpoint that is challenged in the course of a device code flow.
    """

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)
        try:
            start_grant = base_models.CompositionStartRequest(**json_data)
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": f"Malformed request: {str(e)}",
                }
            )

        manifest = start_grant.composition

        try:
            logo = download_logo(manifest.logo) if manifest.logo else None
        except Exception as e:
            logger.error(f"Error downloading logo: {manifest.logo}", exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": "Error downloading logo",
                }
            )

        logger.info(f"Received start challenge for {manifest.identifier}")

        device_code = models.CompositionDeviceCode.objects.create(
            code=logic.create_device_code(),
            challenge_code=logic.create_device_code(),
            manifest=manifest.model_dump(),
            expires_at=datetime.datetime.now() + datetime.timedelta(seconds=start_grant.expiration_time_seconds),
        )

        return JsonResponse(
            data={
                "status": "granted",
                "code": device_code.code,
                "challenge": device_code.challenge_code,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class CompositionChallengeView(View):
    """
    An endpoint that is challenged in the course of a device code flow.
    """

    def post(self, request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
            challenge = base_models.DeviceCodeChallengeRequest(**json_data)
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": f"Malformed request: {str(e)}",
                }
            )
        try:
            device_code = models.CompositionDeviceCode.objects.get(challenge_code=challenge.code)
        except models.CompositionDeviceCode.DoesNotExist:
            return JsonResponse(
                data={
                    "status": "error",
                    "error": "Challenge does not exist",
                }
            )

        if datetime.datetime.now(datetime.timezone.utc) > device_code.expires_at:
            device_code.delete()
            return JsonResponse(
                data={
                    "status": "expired",
                    "message": "The user has not given an answer in enough time",
                }
            )

        if device_code.denied:
            device_code.delete()
            return JsonResponse(
                data={
                    "status": "denied",
                    "message": "The user has denied the request",
                }
            )

        # scopes will only be set if the user has verified the challenge
        if device_code.composition:
            return JsonResponse(
                data={
                    "status": "granted",
                    "token": device_code.composition.token,
                }
            )

        return JsonResponse(
            data={
                "status": "pending",
                "message": "User  has not verfied the challenge",
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class ServiceChallengeView(View):
    """
    An endpoint that is challenged in the course of a device code flow.
    """

    def post(self, request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
            challenge = base_models.DeviceCodeChallengeRequest(**json_data)
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": f"Malformed request: {str(e)}",
                }
            )
        try:
            device_code = models.ServiceDeviceCode.objects.get(challenge_code=challenge.code)
        except models.ServiceDeviceCode.DoesNotExist:
            return JsonResponse(
                data={
                    "status": "error",
                    "error": "Challenge does not exist",
                }
            )

        if datetime.datetime.now(datetime.timezone.utc) > device_code.expires_at:
            device_code.delete()
            return JsonResponse(
                data={
                    "status": "expired",
                    "message": "The user has not given an answer in enough time",
                }
            )

        if device_code.denied:
            device_code.delete()
            return JsonResponse(
                data={
                    "status": "denied",
                    "message": "The user has denied the request",
                }
            )

        # scopes will only be set if the user has verified the challenge
        if device_code.instance:
            return JsonResponse(
                data={
                    "status": "granted",
                    "token": device_code.instance.token,
                }
            )

        return JsonResponse(
            data={
                "status": "pending",
                "message": "User  has not verfied the challenge",
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class ChallengeView(View):
    """
    An endpoint that is challenged in the course of a device code flow.
    """

    def post(self, request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
            challenge = base_models.DeviceCodeChallengeRequest(**json_data)
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": f"Malformed request: {str(e)}",
                }
            )
        try:
            device_code = models.DeviceCode.objects.get(code=challenge.code)
        except models.DeviceCode.DoesNotExist:
            return JsonResponse(
                data={
                    "status": "error",
                    "error": "Challenge does not exist",
                }
            )

        if datetime.datetime.now(datetime.timezone.utc) > device_code.expires_at:
            device_code.delete()
            return JsonResponse(
                data={
                    "status": "expired",
                    "message": "The user has not given an answer in enough time",
                }
            )

        if device_code.denied:
            device_code.delete()
            return JsonResponse(
                data={
                    "status": "denied",
                    "message": "The user has denied the request",
                }
            )

        # scopes will only be set if the user has verified the challenge
        if device_code.client:
            return JsonResponse(
                data={
                    "status": "granted",
                    "token": device_code.client.token,
                }
            )

        return JsonResponse(
            data={
                "status": "pending",
                "message": "User  has not verfied the challenge",
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class RetrieveView(View):
    """
    Implements an endpoint that returns the faktsclaim for a given identifier and version
    if the app was already configured and the app is marked as PUBLIC. While any app can
    request a faktsclaim for any other app, redirect uris are set to predifined values
    and the app will not be able to use the faktsclaim to get a configuration.
    """

    def post(self, request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
            retrieve = base_models.RetrieveRequest(**json_data)
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": f"Malformed request: {str(e)}",
                }
            )

        try:
            app = models.App.objects.get(identifier=retrieve.manifest.identifier)
            release = models.Release.objects.get(app=app, version=retrieve.manifest.version)
        except models.Release.DoesNotExist:
            return JsonResponse(
                data={
                    "status": "error",
                    "message": f"Release does not exist {retrieve.manifest.identifier}:{retrieve.manifest.version}",
                }
            )
        except models.App.DoesNotExist:
            return JsonResponse(
                data={
                    "status": "error",
                    "message": f"App does not exist {retrieve.manifest.identifier}",
                }
            )

        client = release.clients.filter(public=True).first()
        if not client:
            return JsonResponse(
                data={
                    "status": "error",
                    "message": "There is no client for this app that is public. Please use a different grant",
                }
            )

        return JsonResponse(
            data={
                "status": "granted",
                "token": client.token,
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class RedeemView(View):
    """
    Implements an endpoint that returns the faktsclaim for a given identifier and version
    if the app was already configured and the app is marked as PUBLIC. While any app can
    request a faktsclaim for any other app, redirect uris are set to predifined values
    and the app will not be able to use the faktsclaim to get a configuration.
    """

    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)
        try:
            redeem_request = base_models.ReedeemTokenRequest(**json_data)
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "error": f"Malformed request: {str(e)}",
                }
            )

        manifest = redeem_request.manifest
        token = redeem_request.token

        try:
            valid_token = models.RedeemToken.objects.get(token=token)
        except models.RedeemToken.DoesNotExist:
            return JsonResponse(
                data={
                    "status": "error",
                    "message": "Invalid redeem token",
                }
            )
        if valid_token.expires_at:
            if valid_token.expires_at < datetime.datetime.now():
                valid_token.delete()
                return JsonResponse(
                    data={
                        "status": "error",
                        "message": "Redeem token expired",
                    }
                )

        if valid_token.client:
            return JsonResponse(
                data={
                    "status": "granted",
                    "token": valid_token.client.token,
                }
            )

        else:
            try:
                token = logic.validate_redeem_token(
                    redeem_token=valid_token,
                    manifest=manifest,
                )
                return JsonResponse(
                    data={
                        "status": "granted",
                        "token": token.client.token,
                    }
                )
            except Exception as e:
                logger.error(e, exc_info=True)
                return JsonResponse(
                    data={
                        "status": "error",
                        "message": str(e),
                    }
                )


@method_decorator(csrf_exempt, name="dispatch")
class ClaimView(View):
    """
    Implements an endpoint to retrieve a faktsclaim given a
    token that was generated by the platform
    """

    def post(self, request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
            claim = base_models.ClaimRequest(**json_data)
        except Exception as e:
            logger.error(e)
            return JsonResponse(
                data={
                    "status": "error",
                    "message": f"Malformed request: {str(e)}",
                }
            )

        try:
            client = models.Client.objects.get(token=claim.token)

            context = logic.create_linking_context(request, client, claim)

            config = logic.render_composition(client, context)

            return JsonResponse(
                data={
                    "status": "granted",
                    "config": config,
                }
            )
        except models.Client.DoesNotExist:
            return JsonResponse(
                data={
                    "status": "error",
                    "message": "No Client found for this token",
                }
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "message": f"Error creating configuration",
                }
            )


@method_decorator(csrf_exempt, name="dispatch")
class ClaimCompositionView(View):
    """
    Implements an endpoint to retrieve a faktsclaim given a
    token that was generated by the platform
    """

    def post(self, request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
            claim = base_models.ServerClaimRequest(**json_data)
        except Exception as e:
            logger.error(e)
            return JsonResponse(
                data={
                    "status": "error",
                    "message": f"Malformed request: {str(e)}",
                }
            )

        try:
            composition = models.Composition.objects.get(token=claim.token)

            context = logic.create_serverlinking_context(request, composition, claim)

            config = logic.render_server_fakts(composition, context)

            return JsonResponse(
                data={
                    "status": "granted",
                    "config": config.model_dump(),
                }
            )
        except models.Client.DoesNotExist:
            return JsonResponse(
                data={
                    "status": "error",
                    "message": "No Client found for this token",
                }
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "message": f"Error creating configuration",
                }
            )


@method_decorator(csrf_exempt, name="dispatch")
class ReportView(View):
    """
    Implements an endpoint to retrieve a faktsclaim given a
    token that was generated by the platform
    """

    def post(self, request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
            claim = base_models.ReportRequest(**json_data)
        except Exception as e:
            logger.error(e)
            return JsonResponse(
                data={
                    "status": "error",
                    "message": f"Malformed request: {str(e)}",
                }
            )

        try:
            client = models.Client.objects.get(token=claim.token)
            client.functional = claim.functional
            client.save()

            for req_key, alias_report in claim.alias_reports.items():
                alias = models.InstanceAlias.objects.get(id=alias_report.alias_id) if alias_report.alias_id else None

                models.UsedAlias.objects.update_or_create(
                    client=client,
                    key=req_key,
                    defaults={
                        "alias": alias,
                        "valid": alias_report.valid,
                        "reason": alias_report.reason,
                        "used_at": timezone.now(),
                    },
                )

            return JsonResponse(
                data={
                    "status": "reported",
                    "message": "Report processed successfully",
                }
            )
        except models.Client.DoesNotExist:
            return JsonResponse(
                data={
                    "status": "error",
                    "message": "No Client found for this token",
                }
            )
        except Exception as e:
            logger.error(e, exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "message": f"Error creating configuration",
                }
            )
