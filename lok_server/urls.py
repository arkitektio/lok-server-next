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

from django.urls import path, include, re_path


# Bootstrap Backend
def index(request):
    # Render that in the index template
    return render(request, "index.html")

hallo ="hallsssoss"

urlpatterns = [
    dynamicpath("", index, name="index"),
    dynamicpath("admin/", admin.site.urls),
    dynamicpath("f/", include("fakts.urls", namespace="fakts")),
    dynamicpath(".well-known/fakts", WellKnownFakts.as_view()),
    dynamicpath("accounts/", include("karakter.urls")),
    dynamicpath('o/', include('authapp.urls')),  # /auth/login/, /auth/logout/
    

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

