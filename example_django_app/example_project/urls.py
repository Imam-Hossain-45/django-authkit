"""URL configuration for the authkit example app."""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("pages.urls")),
    path("", include("authkit.urls")),
    path("admin/", admin.site.urls),
]
