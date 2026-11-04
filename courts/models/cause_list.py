import uuid
from django.db import models
from .court import Court


class CauseList(models.Model):
    cause_list_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    court = models.ForeignKey(Court, on_delete=models.PROTECT, related_name='cause_lists')
    cause_list_date = models.DateField(db_index=True)
    day_of_week = models.CharField(max_length=30)                                 # Thursday, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cause_lists'
        constraints = [
            models.UniqueConstraint(fields=['court', 'cause_list_date'], name='unique_court_cause_list_date')
        ]

    def __str__(self):
        return f"Cause List for {self.court} on {self.cause_list_date}"
