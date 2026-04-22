"""Views for authkit audit log APIs."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets

from authkit.audit_log.models import AuditLog
from authkit.audit_log.permissions import CanViewAuditLogs
from authkit.audit_log.serializers import AuditLogSerializer


@extend_schema_view(
    list=extend_schema(
        operation_id="authkit_audit_logs_list",
        summary="List audit logs",
        tags=["audit_log"],
    ),
    retrieve=extend_schema(
        operation_id="authkit_audit_logs_retrieve",
        summary="Get audit log detail",
        tags=["audit_log"],
    ),
)
class AuditLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only API for audit logs."""

    queryset = AuditLog.objects.select_related("actor", "target_user").all()
    serializer_class = AuditLogSerializer
    permission_classes = [CanViewAuditLogs]
    http_method_names = ["get", "options", "head"]
