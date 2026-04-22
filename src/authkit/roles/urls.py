"""URL routes for authkit role APIs."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from authkit.roles.views import RoleViewSet

app_name = "roles"

router = SimpleRouter()
router.register("", RoleViewSet, basename="role")

urlpatterns = [
    path("", include(router.urls)),
]
