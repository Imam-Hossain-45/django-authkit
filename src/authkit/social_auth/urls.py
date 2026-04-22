"""URL routes for authkit social authentication APIs."""

from django.urls import path

from authkit.social_auth.views import (
    SocialProviderDetailView,
    SocialProviderListView,
    SocialTokenExchangeView,
)

app_name = "social_auth"

urlpatterns = [
    path("providers/", SocialProviderListView.as_view(), name="provider-list"),
    path(
        "providers/<slug:provider>/",
        SocialProviderDetailView.as_view(),
        name="provider-detail",
    ),
    path(
        "<slug:provider>/token/",
        SocialTokenExchangeView.as_view(),
        name="token-exchange",
    ),
]
