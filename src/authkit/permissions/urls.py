"""URL routes for authkit permission APIs."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from authkit.permissions.views import PermissionViewSet

app_name = "permissions"

router = SimpleRouter()
router.register("", PermissionViewSet, basename="permission")

urlpatterns = [
    path("", include(router.urls)),
]
