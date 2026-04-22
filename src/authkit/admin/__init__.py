"""Django admin integration for authkit."""

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from authkit.models import AuditLog, SocialAccount, User


class AuthKitPermissionAdmin(admin.ModelAdmin):
    """Admin configuration for Django permissions used by authkit."""

    list_display = ("name", "codename", "content_type")
    list_filter = ("content_type__app_label", "content_type__model")
    search_fields = (
        "name",
        "codename",
        "content_type__app_label",
        "content_type__model",
    )
    autocomplete_fields = ("content_type",)
    ordering = ("content_type__app_label", "content_type__model", "codename")


class AuthKitContentTypeAdmin(admin.ModelAdmin):
    """Read-only admin for content types that back Django permissions."""

    list_display = ("app_label", "model")
    list_filter = ("app_label",)
    search_fields = ("app_label", "model")
    ordering = ("app_label", "model")

    def has_add_permission(self, request) -> bool:
        """Content types are maintained by Django migrations."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Content types are maintained by Django migrations."""
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Content types are maintained by Django migrations."""
        return False


if not admin.site.is_registered(Group):
    admin.site.register(Group, GroupAdmin)

if not admin.site.is_registered(Permission):
    admin.site.register(Permission, AuthKitPermissionAdmin)

if not admin.site.is_registered(ContentType):
    admin.site.register(ContentType, AuthKitContentTypeAdmin)


@admin.register(User)
class AuthKitUserAdmin(UserAdmin):
    """Admin configuration for the email-based authkit user model."""

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Status and permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_verified",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                    "is_verified",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "is_verified",
        "date_joined",
        "last_login",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "is_verified", "groups")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined", "updated_at")
    filter_horizontal = ("groups", "user_permissions")


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    """Admin configuration for linked social authentication accounts."""

    list_display = (
        "provider",
        "provider_user_id",
        "user",
        "email",
        "created_at",
        "updated_at",
    )
    list_filter = ("provider", "created_at", "updated_at")
    search_fields = (
        "provider",
        "provider_user_id",
        "email",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user",)
    ordering = ("provider", "email")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only admin for authkit audit logs."""

    list_display = (
        "event_type",
        "actor",
        "target_user",
        "ip_address",
        "created_at",
    )
    list_filter = ("event_type", "created_at")
    search_fields = (
        "event_type",
        "message",
        "actor__email",
        "target_user__email",
        "ip_address",
        "user_agent",
    )
    readonly_fields = (
        "actor",
        "target_user",
        "event_type",
        "message",
        "metadata",
        "ip_address",
        "user_agent",
        "created_at",
    )
    ordering = ("-created_at",)

    def has_add_permission(self, request) -> bool:
        """Audit logs are append-only through code paths, not admin."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Allow viewing existing records without allowing edits."""
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None) -> bool:
        """Audit logs are append-only and cannot be deleted in admin."""
        return False
