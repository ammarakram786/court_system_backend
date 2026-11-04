import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from .case import Case


class CaseMarkingHistory(models.Model):
    class Action(models.TextChoices):
        INITIAL = 'INITIAL', _('Initial Assignment')
        MARK = 'MARK', _('Marked')
        MARK_BACK = 'MARK_BACK', _('Marked Back')

    history_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='marking_history')
    from_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='case_transfers_sent'
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='case_transfers_received'
    )
    action = models.CharField(max_length=20, choices=Action.choices, default=Action.MARK)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'case_marking_history'
        verbose_name = 'Case Marking History'
        verbose_name_plural = 'Case Marking Histories'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.case.case_number} - {self.action} to {self.to_user.name} ({self.created_at})"
