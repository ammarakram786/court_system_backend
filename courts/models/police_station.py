import uuid
from django.db import models


class PoliceStation(models.Model):
    police_station_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    district = models.CharField(max_length=100, default='Rawalpindi')
    name = models.CharField(max_length=150)                       # e.g., 'Waris Khan'
    code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    class Meta:
        db_table = 'police_stations'
        verbose_name = 'Police Station'
        verbose_name_plural = 'Police Stations'

    def __str__(self):
        return f"PS {self.name} ({self.district})"
