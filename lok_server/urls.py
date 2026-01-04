"""
URL configuration for kreature project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.urls import include, path
from fakts.views import WellKnownFakts
from django.shortcuts import render
from django.conf import settings
from kante.path import dynamicpath
from django.conf import settings
from django.conf.urls.static import static
from health_check.views import MainView
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from strawberry.django.views import AsyncGraphQLView
from api.management.schema import schema


def fakts_challenge(request):
    """
    Placeholdesr view for the .well-known/fakts-challenge endpoint.
    This should be replaced with the actual logic to handle the challenge.
    """
    return HttpResponse("Fakts Challenge Endpoint", status=200)


from django.urls import path, include, re_path


# Bootstrap Backend
def index(request):
    # Render that in the index template
    return render(request, "index.html")


def management_schema(request):
    schema_content = schema.as_str().encode("utf-8")

    response = HttpResponse(schema_content, content_type="text/plain")
    response["Content-Length"] = str(len(schema_content))
    return response


hallo = "hallsssoss"

urlpatterns = [
    dynamicpath("", index, name="home"),
    dynamicpath("managementgraphql/", AsyncGraphQLView.as_view(schema=schema)),
    dynamicpath("managementschema/", csrf_exempt(management_schema), name="management_schema"),
    dynamicpath("admin/", admin.site.urls),
    dynamicpath("f/", include("fakts.urls", namespace="fakts")),
    dynamicpath("o/", include("authapp.urls")),  # /auth/login/, /auth/logout/
    dynamicpath("ht", csrf_exempt(MainView.as_view()), name="health_check"),
    dynamicpath("accounts/", include("allauth.urls")),
    dynamicpath("accounts/", include("karakter.urls")),
    dynamicpath("_allauth/", include("allauth.headless.urls")),
    dynamicpath(".well-known/fakts-challenge", fakts_challenge, name="fakts-challenge"),
    dynamicpath(".well-known/fakts", WellKnownFakts.as_view()),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
