import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from .case import Case


class CaseParty(models.Model):
    class PartySide(models.TextChoices):
        PETITIONER = 'PETITIONER', _('Petitioner / Appellant')
        RESPONDENT = 'RESPONDENT', _('Respondent / Defendant')
        STATE = 'STATE', _('The State / Prosecution')

    party_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='parties')
    party_side = models.CharField(max_length=20, choices=PartySide.choices)
    party_name = models.CharField(max_length=255)
    is_primary_party = models.BooleanField(default=False)
    counsel_name = models.CharField(max_length=255, blank=True, null=True)        # Advocate / Wakeel
    cnic = models.CharField(max_length=20, blank=True, null=True)
    contact_number = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'case_parties'
        verbose_name = 'Case Party'
        verbose_name_plural = 'Case Parties'

    def __str__(self):
        return f"{self.party_name} ({self.party_side})"
