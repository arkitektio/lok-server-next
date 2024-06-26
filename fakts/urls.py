from django.urls import re_path

from . import views


app_name = "fakts"

# Basic url patterns for fakts 
# as described in the fakts api documentation
base_urlpatterns = [
    re_path(r"^configure/$", views.ConfigureView.as_view(), name="configure"),
    re_path(r"^retrieve/$", views.RetrieveView.as_view(), name="retrieve"),
    re_path(r"^redeem/$", views.RedeemView.as_view(), name="redeem"),
    re_path(r"^challenge/$", views.ChallengeView.as_view(), name="challenge"),
    re_path(r"^start/$", views.StartChallengeView.as_view(), name="start"),
    re_path(r"^device/$", views.DeviceView.as_view(), name="device"),
    re_path(r"^claim/$", views.ClaimView.as_view(), name="claim"),
]


urlpatterns = base_urlpatterns
