from django.urls import path
from .views import profile, home, organization_detail, change_org, accept_invite, leave_org

hallo = "ss"
urlpatterns = [
    path("profile/", profile, name="profile"),
    path("home/", home, name="home"),
    path("organization/<slug:slug>/", organization_detail, name="organization_detail"),
    path("organization/<slug:slug>/leave/", leave_org, name="leave_org"),
    path("changeorg/", change_org, name="karakter_changeorg"),
    path("invite/<uuid:token>/", accept_invite, name="accept_invite"),
]
