"""URL routes for authkit user APIs."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from authkit.users.views import AdminUserViewSet, CurrentUserView

app_name = "users"

router = SimpleRouter()
router.register("", AdminUserViewSet, basename="user")

urlpatterns = [
    path("me/", CurrentUserView.as_view(), name="me"),
    path("", include(router.urls)),
]
