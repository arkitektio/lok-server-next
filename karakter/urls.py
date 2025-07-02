from django.urls import path
from .views import profile, home

hallo = "ss"
urlpatterns = [
    path("profile/", profile, name="profile"),
    path("home/", home, name="home"),
]
