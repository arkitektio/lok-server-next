# authapp/urls.py
from django.urls import path
from .views import CustomLoginView, logout_view, home_view, issue_token, jwks, user_info, open_id_configuration

urlpatterns = [
    path("home/", home_view, name="home"),
    path("token/", issue_token, name="token"),  # Token endpoint
    path("jwks/", jwks, name="jwks"),  # JWKS endpoint
    path("user_info/", user_info, name="user_info"),  # User Info endpoint
]
