import uuid
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel


class PermissionOverride(TimeStampedModel):
    class Effect(models.TextChoices):
        ALLOW = 'ALLOW', _('Allow')
        DENY = 'DENY', _('Deny')

    override_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='permission_overrides',
        db_column='user_id'
    )
    permission_code = models.CharField(max_length=100, db_index=True)
    effect = models.CharField(max_length=10, choices=Effect.choices)
    reason = models.TextField()
    granted_by = models.CharField(max_length=200)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'permission_overrides'
        verbose_name = 'Permission Override'
        verbose_name_plural = 'Permission Overrides'
        constraints = [
            models.UniqueConstraint(fields=['user', 'permission_code'], name='unique_user_permission_override')
        ]

    @property
    def id(self):
        return self.override_id

    def __str__(self):
        return f"{self.user} - {self.permission_code} ({self.effect})"
