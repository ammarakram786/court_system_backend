import uuid
from django.db import models

from core.models import TimeStampedModel
from .permission import Permission


class Role(TimeStampedModel):
    role_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles'
    )

    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']

    @property
    def id(self):
        return self.role_id

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column='role_id')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, db_column='permission_id')

    class Meta:
        db_table = 'role_permissions'
        constraints = [
            models.UniqueConstraint(fields=['role', 'permission'], name='unique_role_permission')
        ]
