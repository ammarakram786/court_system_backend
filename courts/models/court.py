import uuid
from django.db import models


class Court(models.Model):
    court_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    district = models.CharField(max_length=100, default='Rawalpindi')
    court_name = models.CharField(max_length=255)                  # e.g., 'Sessions Court'
    presiding_officer = models.CharField(max_length=255)          # e.g., 'Syed Asghar Ali'
    designation = models.CharField(max_length=150)                # e.g., 'District & Sessions Judge'
    court_room_no = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courts'
        verbose_name = 'Court'
        verbose_name_plural = 'Courts'

    def __str__(self):
        return f"{self.court_name} - {self.presiding_officer}"
