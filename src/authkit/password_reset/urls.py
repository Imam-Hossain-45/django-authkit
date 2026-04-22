"""URL routes for authkit password reset APIs."""

from django.urls import path

from authkit.password_reset.views import (
    PasswordResetConfirmView,
    PasswordResetRequestView,
)

app_name = "password_reset"

urlpatterns = [
    path("request/", PasswordResetRequestView.as_view(), name="request"),
    path("confirm/", PasswordResetConfirmView.as_view(), name="confirm"),
]
