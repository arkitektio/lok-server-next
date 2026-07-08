from django.urls import re_path

from . import views


app_name = "fakts"


def index(request):
    # Render that in the index template
    raise NotImplementedError("This view is not implemented yet.")


# Basic url patterns for fakts
# App-facing API endpoints only (user-facing views are handled by React frontend)
base_urlpatterns = [
    re_path(r"^$", index, name="index"),
    re_path(r"^retrieve/$", views.RetrieveView.as_view(), name="retrieve"),
    re_path(r"^report/$", views.ReportView.as_view(), name="report"),
    re_path(r"^redeem/$", views.RedeemView.as_view(), name="redeem"),
    re_path(r"^challenge/$", views.ChallengeView.as_view(), name="challenge"),
    re_path(r"^servicechallenge/$", views.ServiceChallengeView.as_view(), name="servicechallenge"),
    re_path(r"^hubchallenge/$", views.HubChallengeView.as_view(), name="hubchallenge"),
    re_path(r"^hubstart/$", views.HubStartChallengeView.as_view(), name="hubstart"),
    re_path(r"^start/$", views.StartChallengeView.as_view(), name="start"),
    re_path(r"^servicestart/$", views.ServiceStartChallengeView.as_view(), name="servicestart"),
    re_path(r"^meshstart/$", views.MeshStartChallengeView.as_view(), name="meshstart"),
    re_path(r"^meshchallenge/$", views.MeshChallengeView.as_view(), name="meshchallenge"),
    re_path(r"^claim/$", views.ClaimView.as_view(), name="claim"),
    re_path(r"^claimhub/$", views.ClaimHubView.as_view(), name="hubclaim"),
]


urlpatterns = base_urlpatterns
