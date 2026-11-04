import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class CaseCategory(models.Model):
    class CaseNature(models.TextChoices):
        CIVIL = 'CIVIL', _('Civil')
        CRIMINAL = 'CRIMINAL', _('Criminal')

    category_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nature = models.CharField(max_length=20, choices=CaseNature.choices)
    name = models.CharField(max_length=150)                       # e.g., 'Civil Appeal', 'Criminal Misc'
    short_code = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'case_categories'
        verbose_name = 'Case Category'
        verbose_name_plural = 'Case Categories'

    def __str__(self):
        return f"{self.nature} - {self.name}"
