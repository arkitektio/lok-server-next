from django.urls import path
from .views import profile

hallo = "ss"
urlpatterns = [
    path("profile/", profile, name="profile"),
]
