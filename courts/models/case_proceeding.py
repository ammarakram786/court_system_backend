import uuid
from django.db import models
from accounts.models import User
from .case import Case
from .court import Court


class CaseProceeding(models.Model):
    proceeding_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='proceedings')
    court = models.ForeignKey(Court, on_delete=models.PROTECT, related_name='proceedings')

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_proceedings'
    )

    sr_no = models.PositiveIntegerField()                                         # 1, 2, 3, 4
    proceeding_date = models.DateField(db_index=True)                             # Date of hearing
    stage = models.CharField(max_length=150)                                      # Notice, Summon for Record, Argument
    today_action = models.CharField(max_length=255, blank=True, null=True)       # Notice Issued, Decided
    short_order = models.TextField(blank=True, null=True)                         # Order sheet content
    is_case_decided = models.BooleanField(default=False)

    # Next Adjournment
    next_proceeding_date = models.DateField(null=True, blank=True, db_index=True)
    next_stage_purpose = models.CharField(max_length=255, blank=True, null=True) # Arguments, Production of record

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'case_proceedings'
        verbose_name = 'Case Proceeding'
        verbose_name_plural = 'Case Proceedings'
        ordering = ['case', 'sr_no']
        constraints = [
            models.UniqueConstraint(fields=['case', 'sr_no'], name='unique_case_proceeding_sr_no')
        ]

    def __str__(self):
        return f"Proceeding #{self.sr_no} for Case {self.case.case_number} on {self.proceeding_date}"
