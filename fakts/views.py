from dataclasses import dataclass
from typing import Any, Optional
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import  HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, View, TemplateView
from .forms import ConfigureForm, DeviceForm
from .errors import ConfigurationRequestMalformed, ConfigurationError
import logging
import json
from typing import List
import datetime
from .utils import (
    download_logo,
)
from django.urls import reverse
from django.utils import timesince
from django.shortcuts import redirect
from fakts import base_models, enums, models, builders, logic
from django.conf import settings

import uuid
logger = logging.getLogger(__name__)




@method_decorator(csrf_exempt, name="dispatch")
class WellKnownFakts(View):
    """Well Known fakts Viewset (only allows get). Sends
    back the well known configuration for the fakts server Describing
    endpoints for "Claim" and "Configure" as well as the name and version.
    Of the Fakts Protocol"""




    def get(self, request, format=None):

        with open(settings.CA_FILE, "r") as f:
            ca = f.read()




        return JsonResponse(data={"name": settings.DEPLOYMENT_NAME, "version": "0.0.1", "description": "This is the best servesssr", "claim": request.build_absolute_uri(reverse("fakts:claim")) , "base_url": request.build_absolute_uri(reverse("fakts:index")), "ca_crt" : ca})





class ConfigureView(LoginRequiredMixin, FormView):
    """
    Implements an endpoint to handle *Authorization Requests* as in :rfc:`4.1.1` and prompting the
    user with a form to determine if she authorizes the client application to access her data.
    This endpoint is reached two times during the authorization process:
    * first receive a ``GET`` request from user asking authorization for a certain client
    application, a form is served possibly showing some useful info and prompting for
    *authorize/do not authorize*.

    * then receive a ``POST`` request possibly after user authorized the access

    Some informations contained in the ``GET`` request and needed to create a Grant token during
    the ``POST`` request would be lost between the two steps above, so they are temporarily stored in
    hidden fields on the form.
    A possible alternative could be keeping such informations in the session.

    The endpoint is used in the following flows:
    * Authorization code
    * Implicit grant
    """

    template_name = "fakts/configure.html"
    form_class = ConfigureForm


    def validate_configure_request(self, request) -> base_models.ConfigurationRequest:
        """
        Validate the configure request.
        """
        if request.method != "GET":
            raise ConfigurationRequestMalformed("Only GET requests are allowed")

        claim = request.GET.get("claim", None)
        grant = request.GET.get("grant", None)
        device_code = request.GET.get("device_code", None)

        return base_models.ConfigurationRequest(claim=claim, grant=grant, device_code=device_code)

    def get_initial(self):
        # TODO: move this scopes conversion from and to string into a utils function

        initial_data = {
            "device_code": self.request.GET.get("device_code", None),
        }


        return initial_data
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        the_code =  self.request.GET.get("device_code", None)
        if the_code:

            logger.info(f"Received Context for {the_code}")


            x = models.DeviceCode.objects.get(code=the_code)


            manifest = base_models.Manifest(**x.staging_manifest)


            composition_errors, composition_warnings = logic.check_compability(manifest)
            if len(composition_errors) > 0:
                context["composition_valid"] = False
            else:
                context["composition_valid"] = True


            print(manifest.requirements)

            context["composition_requirements"] = {req.key: req.service for req in manifest.requirements}
            context["composition_errors"] = composition_errors
            context["composition_warnings"] = composition_warnings
            context["staging_identifier"] = x.staging_manifest["identifier"]
            context["staging_version"] = x.staging_manifest["version"]
            context["staging_kind"] = x.staging_kind
            context["staging_redirect_uris"] = x.staging_redirect_uris
            context["staging_scopes"] = x.staging_manifest["scopes"]
            context["staging_logo"] = x.staging_manifest.get("logo", None)

            context["code"] = x







            app = models.App.objects.filter(identifier=x.staging_manifest["identifier"]).first()
            if app:
                context["app"] = app
                release = models.Release.objects.filter(app=app, version=x.staging_manifest["version"]).first()
                if release:
                    context["release"] = release
                    client = models.Client.objects.filter(release=release, kind=x.staging_kind, tenant=self.request.user, redirect_uris=" ".join(x.staging_redirect_uris)).first()
                    if client:
                        context["client"] = client


            

        return context
    
    def form_invalid(self, form: Any) -> HttpResponse:
        print("form invalid")
        return super().form_invalid(form)

    def form_valid(self, form):

        action = self.request.POST.get("action", None)


        device_code = form.cleaned_data["device_code"]


        if action == "allow":

            device_code = models.DeviceCode.objects.get(
                code=device_code,
            )

            manifest = base_models.Manifest(**device_code.staging_manifest)


            redirect_uris = " ".join(device_code.staging_redirect_uris),



            client = models.Client.objects.filter(release__app__identifier=device_code.staging_manifest["identifier"], release__version=device_code.staging_manifest["version"], kind=device_code.staging_kind, tenant=self.request.user, redirect_uris=redirect_uris).first()
                

            if not client:

                token = logic.create_api_token()

                manifest = base_models.Manifest(**device_code.staging_manifest)
                config = None

                if device_code.staging_kind == enums.ClientKindVanilla.DEVELOPMENT.value:
                    config = base_models.DevelopmentClientConfig(
                        kind=enums.ClientKindVanilla.DEVELOPMENT.value,
                        token=token,
                        user=self.request.user.username,
                        tenant=self.request.user.username,
                    )

                elif device_code.staging_kind == enums.ClientKindVanilla.DESKTOP.value:
                    config = base_models.DesktopClientConfig(
                        kind=enums.ClientKindVanilla.DESKTOP.value,
                        token=token,
                        user=self.request.user.username,
                        tenant=self.request.user.username,
                    )

                elif device_code.staging_kind == enums.ClientKindVanilla.WEBSITE.value:
                    config = base_models.WebsiteClientConfig(
                        kind=enums.ClientKindVanilla.WEBSITE.value,
                        token=token,
                        tenant=self.request.user.username,
                        redirect_uris=device_code.staging_redirect_uris,
                        public=device_code.staging_public,
                    )
                else:
                    raise Exception("Unknown client kind")

            
                client = builders.create_client(
                    manifest=manifest,
                    config=config,
                )

            device_code.client = client
            device_code.save()

            return redirect(reverse("fakts:success"))

        else:
            device_code = models.DeviceCode.objects.get(
                code=device_code,
            )

            device_code.denied = True
            device_code.save()

            return redirect(reverse("fakts:failure"))

        


    def get(self, request, *args, **kwargs):
        try:
            configuration = self.validate_configure_request(request)
        except ConfigurationError as error:
            # Application is not available at this time.
            return self.error_response(error, application=None)

        kwargs["grant"] = configuration.grant

        if configuration.grant == enums.FaktsGrantKind.DEVICE_CODE.value:
            if not configuration.device_code:
                raise ConfigurationError("No device code provided")

            kwargs["device_code"] = configuration.device_code
            challenge = models.DeviceCode.objects.get(
                code=configuration.device_code,
            )


            kwargs["staging_public"] = challenge.staging_public
            kwargs["created_at"] = timesince.timesince(challenge.created_at)

        # following two loc are here only because of https://code.djangoproject.com/ticket/17795
        form = self.get_form(self.get_form_class())
        kwargs["form"] = form
        kwargs["grant"] = configuration.grant


        # Check to see if the user has already granted access and return
        # a successful response depending on "approval_prompt" url parameter

        return self.render_to_response(self.get_context_data(**kwargs))


class DeviceView(LoginRequiredMixin, FormView):
    """
    This is the start view for the device flow.
    It will redirect to the device code view.
    """

    template_name = "fakts/device.html"
    form_class = DeviceForm

    def get_initial(self):
        initial_data = {
            "device_code": self.request.GET.get("device_code", None),
        }

        return initial_data

    def form_valid(self, form):
        device_code = form.cleaned_data["device_code"]

        return redirect(f"/f/configure/?grant=device_code&device_code={device_code}")

    def get(self, request, *args, **kwargs):
        # following two loc are here only because of https://code.djangoproject.com/ticket/17795
        form = self.get_form(self.get_form_class())
        kwargs["form"] = form

        return self.render_to_response(self.get_context_data(**kwargs))
    

class SuccessView(LoginRequiredMixin, TemplateView):
    """
    This is the start view for the device flow.
    It will redirect to the device code view.
    """

    template_name = "fakts/success.html"


    def get(self, request, *args, **kwargs):

        return self.render_to_response(self.get_context_data(**kwargs))

class FailureView(LoginRequiredMixin, TemplateView):
    """
    This is the start view for the device flow.
    It will redirect to the device code view.
    """

    template_name = "fakts/denied.html"


    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))



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
            expires_at=datetime.datetime.now(timezone.utc) + datetime.timedelta(seconds=start_grant.expiration_time_seconds),
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
        

        if datetime.datetime.now(timezone.utc) > device_code.expires_at:
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
            if valid_token.expires_at < datetime.datetime.now(timezone.utc):
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
                token = logic.create_api_token()

                config = None

                config = base_models.DevelopmentClientConfig(
                    kind=enums.ClientKindVanilla.DEVELOPMENT.value,
                    token=token,
                    user=valid_token.user.username,
                    tenant=valid_token.user.username,
                )

                
                client = builders.create_client(
                    manifest=manifest,
                    config=config,
                )

                valid_token.client = client
                valid_token.save()

                return JsonResponse(
                    data={
                        "status": "granted",
                        "token": client.token,
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

            if claim.composition:
                try:
                    composition = models.Composition.objects.get(name=claim.composition)
                except models.Composition.DoesNotExist:
                    return JsonResponse(
                        data={
                            "status": "error",
                            "message": f'Template {claim.composition} does not exist',
                        }
                    )
            else:
                composition = client.composition

            config = logic.render_composition(composition, context)

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
            logger.error(e , exc_info=True)
            return JsonResponse(
                data={
                    "status": "error",
                    "message": f"Error creating configuration",
                }
            )