import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from organizations.models import Organization
from users.models import User

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
        unique_together = ('case', 'sr_no')

    def __str__(self):
        return f"Proceeding #{self.sr_no} for Case {self.case.case_number} on {self.proceeding_date}"


class CauseList(models.Model):
    cause_list_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    court = models.ForeignKey(Court, on_delete=models.PROTECT, related_name='cause_lists')
    cause_list_date = models.DateField(db_index=True)
    day_of_week = models.CharField(max_length=30)                                 # Thursday, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cause_lists'
        unique_together = ('court', 'cause_list_date')

    def __str__(self):
        return f"Cause List for {self.court} on {self.cause_list_date}"


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
        unique_together = ('cause_list', 'roster_sr_no')

    def __str__(self):
        return f"Roster #{self.roster_sr_no} - Case {self.case.case_number}"
