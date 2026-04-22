# Generated manually for the initial authkit audit log model.

import uuid

import django.conf
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authkit", "0002_socialaccount"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        db_index=True,
                        max_length=100,
                        verbose_name="event type",
                    ),
                ),
                ("message", models.TextField(blank=True, verbose_name="message")),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        verbose_name="metadata",
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True,
                        null=True,
                        verbose_name="IP address",
                    ),
                ),
                ("user_agent", models.TextField(blank=True, verbose_name="user agent")),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        verbose_name="created at",
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="authkit_actor_audit_logs",
                        to=django.conf.settings.AUTH_USER_MODEL,
                        verbose_name="actor",
                    ),
                ),
                (
                    "target_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="authkit_target_audit_logs",
                        to=django.conf.settings.AUTH_USER_MODEL,
                        verbose_name="target user",
                    ),
                ),
            ],
            options={
                "verbose_name": "audit log",
                "verbose_name_plural": "audit logs",
                "ordering": ["-created_at"],
            },
        ),
    ]
