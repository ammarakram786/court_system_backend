import uuid
from django.db import models

from core.models import TimeStampedModel


class Permission(TimeStampedModel):
    permission_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    app_name = models.CharField(max_length=100, db_index=True, default='accounts')
    module_name = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=150)
    code_name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['app_name', 'module_name', 'name']

    def __init__(self, *args, **kwargs):
        if 'code' in kwargs and 'code_name' not in kwargs:
            kwargs['code_name'] = kwargs.pop('code')
        if 'module' in kwargs and 'module_name' not in kwargs:
            kwargs['module_name'] = kwargs.pop('module')
        super().__init__(*args, **kwargs)

    @property
    def id(self):
        return self.permission_id

    @property
    def code(self):
        return self.code_name

    @code.setter
    def code(self, value):
        self.code_name = value

    @property
    def module(self):
        return self.module_name

    @module.setter
    def module(self, value):
        self.module_name = value

    def __str__(self):
        return f"[{self.app_name} | {self.module_name}] {self.name} ({self.code_name})"
