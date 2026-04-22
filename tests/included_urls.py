"""URLConf that includes authkit like a consumer project."""

from django.urls import include, path

urlpatterns = [
    path("", include("authkit.urls")),
]
