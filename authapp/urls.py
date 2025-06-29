# authapp/urls.py
from django.urls import path
from .views import CustomLoginView, logout_view, home_view, issue_token

urlpatterns = [
    path("home/", home_view, name="home"),
    path("token/", issue_token, name="token"),  # Token endpoint
]
