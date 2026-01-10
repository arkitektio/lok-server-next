from django.urls import re_path

from . import views


app_name = "fakts"

hallo = "hallsssos"


def index(request):
    # Render that in the index template
    raise NotImplementedError("This view is not implemented yet.")


# Basic url patterns for fakts
# as described in the fakts api documentation
base_urlpatterns = [
    re_path(r"^$", index, name="index"),
    re_path(r"^configure/$", views.ConfigureView.as_view(), name="configure"),
    re_path(r"^retrieve/$", views.RetrieveView.as_view(), name="retrieve"),
    re_path(r"^report/$", views.ReportView.as_view(), name="report"),
    re_path(r"^redeem/$", views.RedeemView.as_view(), name="redeem"),
    re_path(r"^challenge/$", views.ChallengeView.as_view(), name="challenge"),
    re_path(r"^servicechallenge/$", views.ServiceChallengeView.as_view(), name="servicechallenge"),
    re_path(r"^compositionchallenge/$", views.CompositionChallengeView.as_view(), name="compositionchallenge"),
    re_path(r"^compositionstart/$", views.CompositionStartChallengeView.as_view(), name="compositionstart"),
    re_path(r"^start/$", views.StartChallengeView.as_view(), name="start"),
    re_path(r"^servicestart/$", views.ServiceStartChallengeView.as_view(), name="servicestart"),
    re_path(r"^device/$", views.DeviceView.as_view(), name="device"),
    re_path(r"^claim/$", views.ClaimView.as_view(), name="claim"),
    re_path(r"^success/$", views.SuccessView.as_view(), name="success"),
    re_path(r"^failure/$", views.FailureView.as_view(), name="failure"),
]


urlpatterns = base_urlpatterns
