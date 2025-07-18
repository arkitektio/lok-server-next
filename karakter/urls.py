from django.urls import path
from .views import profile, home, organization_detail, change_org

hallo = "ss"
urlpatterns = [
    path("profile/", profile, name="profile"),
    path("home/", home, name="home"),
    path("organization/<slug:slug>/", organization_detail, name="organization_detail"),
    path("changeorg/", change_org, name="karakter_changeorg"),
]
