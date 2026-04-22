"""URL routes for authkit email verification APIs."""

from django.urls import path

from authkit.verification.views import (
    VerificationConfirmView,
    VerificationRequestView,
)

app_name = "verification"

urlpatterns = [
    path("request/", VerificationRequestView.as_view(), name="request"),
    path("confirm/", VerificationConfirmView.as_view(), name="confirm"),
]
