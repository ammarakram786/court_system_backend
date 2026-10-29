import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Organization(models.Model):
    """
    Hierarchical structure for branches, directorates, and legal cells.
    Strict constraint: Exactly ONE root organization is permitted (parent=None).
    """
    organization_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_organization = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='sub_organizations',
        db_column='parent_organization_id'
    )
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    org_level = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organizations'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        ordering = ['org_level', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['parent_organization'],
                condition=models.Q(parent_organization__isnull=True),
                name='unique_single_root_organization'
            )
        ]

    def clean(self):
        super().clean()
        if self.parent_organization is None:
            existing_root = Organization.objects.filter(parent_organization__isnull=True)
            if self.pk:
                existing_root = existing_root.exclude(pk=self.pk)
            if existing_root.exists():
                raise ValidationError(
                    _("Only one root organization is allowed. Please specify a parent organization.")
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.parent_organization:
            self.org_level = self.parent_organization.org_level + 1
        else:
            self.org_level = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Rank(models.Model):
    rank_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=20, blank=True, null=True)
    seniority_index = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ranks'
        verbose_name = 'Rank'
        verbose_name_plural = 'Ranks'
        ordering = ['seniority_index']

    def __str__(self):
        return f"{self.title} ({self.abbreviation})" if self.abbreviation else self.title


class Appointment(models.Model):
    appointment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150, unique=True)
    appointment_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appointments'
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'

    def __str__(self):
        return self.title
