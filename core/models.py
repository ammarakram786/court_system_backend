from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserTimeStampedModel(TimeStampedModel):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_created',
        on_delete=models.CASCADE
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_updated',
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
