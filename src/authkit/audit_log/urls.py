"""URL routes for authkit audit log APIs."""

from django.urls import include, path
from rest_framework.routers import SimpleRouter

from authkit.audit_log.views import AuditLogViewSet

app_name = "audit_log"

router = SimpleRouter()
router.register("", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("", include(router.urls)),
]
