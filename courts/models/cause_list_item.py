import uuid
from django.db import models
from .court import Court
from .cause_list import CauseList
from .case import Case
from .case_proceeding import CaseProceeding


class CauseListItem(models.Model):
    item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cause_list = models.ForeignKey(CauseList, on_delete=models.CASCADE, related_name='items')
    case = models.ForeignKey(Case, on_delete=models.PROTECT, related_name='cause_list_entries')
    proceeding = models.ForeignKey(CaseProceeding, on_delete=models.PROTECT, related_name='cause_list_entries')
    roster_sr_no = models.PositiveIntegerField()                                  # Serial number in roster
    category_heading = models.CharField(max_length=150)                           # e.g., 'Criminal Misc'

    class Meta:
        db_table = 'cause_list_items'
        ordering = ['roster_sr_no']
        constraints = [
            models.UniqueConstraint(fields=['cause_list', 'roster_sr_no'], name='unique_cause_list_roster_sr_no')
        ]

    def __str__(self):
        return f"Roster #{self.roster_sr_no} - Case {self.case.case_number}"
