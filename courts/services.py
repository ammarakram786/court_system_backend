from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from accounts.models import User
from .models import (
    Court, PoliceStation, CaseCategory, Case, CaseParty, CaseProceeding,
    CauseList, CauseListItem, CaseMarkingHistory
)

def court_create(*, district='Rawalpindi', court_name, presiding_officer, designation, court_room_no=None, is_active=True) -> Court:
    return Court.objects.create(
        district=district,
        court_name=court_name,
        presiding_officer=presiding_officer,
        designation=designation,
        court_room_no=court_room_no,
        is_active=is_active
    )

def police_station_create(*, district='Rawalpindi', name, code=None) -> PoliceStation:
    return PoliceStation.objects.create(district=district, name=name, code=code)

def case_category_create(*, nature, name, short_code=None) -> CaseCategory:
    return CaseCategory.objects.create(nature=nature, name=name, short_code=short_code)

@transaction.atomic
def case_create(*, case_number: str, case_title: str, court: Court, category: CaseCategory, managing_organization, institution_date, **kwargs) -> Case:
    case = Case.objects.create(
        case_number=case_number,
        case_title=case_title,
        court=court,
        category=category,
        managing_organization=managing_organization,
        institution_date=institution_date,
        **kwargs
    )
    return case

@transaction.atomic
def case_update(*, case: Case, **kwargs) -> Case:
    for field, value in kwargs.items():
        setattr(case, field, value)
    case.full_clean()
    case.save()
    return case

def case_party_create(*, case: Case, party_side: str, party_name: str, is_primary_party: bool = False, **kwargs) -> CaseParty:
    return CaseParty.objects.create(
        case=case,
        party_side=party_side,
        party_name=party_name,
        is_primary_party=is_primary_party,
        **kwargs
    )

@transaction.atomic
def case_proceeding_create(*, case: Case, court: Court, sr_no: int = None, proceeding_date, stage: str, **kwargs) -> CaseProceeding:
    if sr_no is None:
        from django.db.models import Max
        max_sr = CaseProceeding.objects.filter(case=case).aggregate(Max('sr_no'))['sr_no__max'] or 0
        sr_no = max_sr + 1

    proceeding = CaseProceeding.objects.create(
        case=case,
        court=court,
        sr_no=sr_no,
        proceeding_date=proceeding_date,
        stage=stage,
        **kwargs
    )
    if proceeding.is_case_decided:
        case.status = Case.CaseStatus.DECIDED
        case.decision_date = proceeding_date
        case.save(update_fields=['status', 'decision_date', 'updated_at'])
    return proceeding

def cause_list_create(*, court: Court, cause_list_date, day_of_week: str) -> CauseList:
    return CauseList.objects.create(
        court=court,
        cause_list_date=cause_list_date,
        day_of_week=day_of_week
    )

def cause_list_item_create(*, cause_list: CauseList, case: Case, proceeding: CaseProceeding, roster_sr_no: int, category_heading: str) -> CauseListItem:
    return CauseListItem.objects.create(
        cause_list=cause_list,
        case=case,
        proceeding=proceeding,
        roster_sr_no=roster_sr_no,
        category_heading=category_heading
    )


@transaction.atomic
def case_mark(*, case: Case, from_user: User, to_user: User, remarks: str = "") -> Case:
    if case.status in [Case.CaseStatus.DECIDED, Case.CaseStatus.DISPOSED, Case.CaseStatus.CONSIGNED]:
        raise ValidationError("Cannot mark a closed or decided case.")
    if not to_user.is_active or getattr(to_user, 'profile_status', 'ACTIVE') != 'ACTIVE':
        raise ValidationError("Target officer is not active.")
    if to_user.user_id == case.assigned_case_officer_id:
        raise ValidationError("Case is already marked to this officer.")

    CaseMarkingHistory.objects.create(
        case=case,
        from_user=from_user,
        to_user=to_user,
        action=CaseMarkingHistory.Action.MARK,
        remarks=remarks
    )

    case.marked_by = from_user
    case.assigned_case_officer = to_user
    case.marked_at = timezone.now()
    case.marking_remarks = remarks
    case.save(update_fields=['marked_by', 'assigned_case_officer', 'marked_at', 'marking_remarks', 'updated_at'])
    return case


@transaction.atomic
def case_mark_back(*, case: Case, from_user: User, remarks: str = "") -> Case:
    if not case.marked_by:
        raise ValidationError("Cannot mark back: No previous marking officer found for this case.")
    if case.status in [Case.CaseStatus.DECIDED, Case.CaseStatus.DISPOSED, Case.CaseStatus.CONSIGNED]:
        raise ValidationError("Cannot mark back a closed or decided case.")

    target_user = case.marked_by
    if not target_user.is_active or getattr(target_user, 'profile_status', 'ACTIVE') != 'ACTIVE':
        raise ValidationError(f"Cannot mark back: Officer {target_user.name} is no longer active.")

    CaseMarkingHistory.objects.create(
        case=case,
        from_user=from_user,
        to_user=target_user,
        action=CaseMarkingHistory.Action.MARK_BACK,
        remarks=remarks
    )

    case.assigned_case_officer = target_user
    case.marked_by = from_user
    case.marked_at = timezone.now()
    case.marking_remarks = remarks
    case.save(update_fields=['marked_by', 'assigned_case_officer', 'marked_at', 'marking_remarks', 'updated_at'])
    return case

