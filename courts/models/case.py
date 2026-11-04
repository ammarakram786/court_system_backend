import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import Organization, User
from .court import Court
from .case_category import CaseCategory
from .police_station import PoliceStation


class Case(models.Model):
    class CaseStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        DECIDED = 'DECIDED', _('Decided')
        DISPOSED = 'DISPOSED', _('Disposed')
        TRANSFERRED = 'TRANSFERRED', _('Transferred')
        CONSIGNED = 'CONSIGNED', _('Consigned to Record')

    case_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_number = models.CharField(max_length=100, unique=True, db_index=True) # e.g., 241259126
    case_title = models.CharField(max_length=500)                              # e.g., Muhammad Yaseen VS Punjab Health Care Commission

    # Forum & Classification
    court = models.ForeignKey(Court, on_delete=models.PROTECT, related_name='cases')
    category = models.ForeignKey(CaseCategory, on_delete=models.PROTECT, related_name='cases')

    # Application Organizational Ownership & Case Officer Assignment
    managing_organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='managed_cases'
    )
    assigned_case_officer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases'
    )
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_cases'
    )
    marked_at = models.DateTimeField(null=True, blank=True)
    marking_remarks = models.TextField(blank=True, null=True)

    # Institution Particulars
    institution_number = models.CharField(max_length=100, blank=True, null=True) # e.g., 2981
    institution_date = models.DateField(db_index=True)                            # e.g., 2026-09-26

    # Criminal/FIR Particulars
    police_station = models.ForeignKey(PoliceStation, on_delete=models.SET_NULL, null=True, blank=True, related_name='cases')
    fir_number = models.CharField(max_length=50, blank=True, null=True)          # e.g., 1656
    fir_year = models.PositiveSmallIntegerField(blank=True, null=True)           # e.g., 2023
    offence_sections = models.CharField(max_length=255, blank=True, null=True)   # e.g., PPC 302

    # Status
    status = models.CharField(max_length=30, choices=CaseStatus.choices, default=CaseStatus.PENDING, db_index=True)
    decision_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cases'
        verbose_name = 'Case'
        verbose_name_plural = 'Cases'
        indexes = [
            models.Index(fields=['police_station', 'fir_year', 'fir_number'], name='idx_case_fir_lookup'),
        ]

    def __str__(self):
        return f"{self.case_number} - {self.case_title}"
